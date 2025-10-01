# Drop-in Django module:
# - Add to urls.py:
#     from scripts.analytics_views import urlpatterns as analytics_urlpatterns
#     urlpatterns += [ path("analytics/", include((analytics_urlpatterns, "analytics"))) ]
#
# - Set environment variable POSTGRES_URL to your database URL.
#   Example: export POSTGRES_URL="postgresql://user:pass@host:port/db"
#
# Endpoints:
#   GET /analytics/data?range=today|yesterday|week|month|custom&start=YYYY-MM-DD&end=YYYY-MM-DD
#   GET /analytics/chart/<chart_type>?same query params as above
#     chart_type in {order-status, top-menu, menu-by-hour, day-wise-menu, day-wise-orders-revenue}

import os
import io
import json
import base64
import math
import datetime as dt
from typing import Tuple, Dict, Any, List, Optional

from django.http import JsonResponse, HttpResponse
from django.urls import path
from django.utils.timezone import utc

# Prefer psycopg2 if installed with Django; fall back to psycopg (v3) if needed.
try:
    import psycopg2 as psycopg
    from psycopg2.extras import DictCursor
    def _connect(dsn): return psycopg.connect(dsn)
except Exception:  # pragma: no cover
    import psycopg
    from psycopg.rows import dict_row
    def _connect(dsn): return psycopg.connect(dsn, row_factory=dict_row)

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt

POSTGRES_URL = os.environ.get("POSTGRES_URL") or os.environ.get("DATABASE_URL")

def _get_conn():
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL (or DATABASE_URL) is not set")
    return _connect(POSTGRES_URL)

def _date_range(params) -> Tuple[dt.datetime, dt.datetime]:
    """Compute [start, end) UTC for given query params."""
    today = dt.datetime.utcnow().date()
    rng = (params.get("range") or "today").lower()

    def as_utc(d: dt.date) -> dt.datetime:
        return dt.datetime(d.year, d.month, d.day, tzinfo=utc)

    if rng == "today":
        start = as_utc(today)
        end = start + dt.timedelta(days=1)
    elif rng == "yesterday":
        start = as_utc(today - dt.timedelta(days=1))
        end = as_utc(today)
    elif rng == "week":
        # ISO week starting Monday
        start = as_utc(today - dt.timedelta(days=today.weekday()))
        end = as_utc(today + dt.timedelta(days=1))
    elif rng == "month":
        start = as_utc(today.replace(day=1))
        # next month
        if start.month == 12:
            end = as_utc(dt.date(start.year + 1, 1, 1))
        else:
            end = as_utc(dt.date(start.year, start.month + 1, 1))
        # clamp to today+1 so "current month"
        end = min(end, as_utc(today + dt.timedelta(days=1)))
    else:
        # custom
        s = params.get("start")
        e = params.get("end")
        if not s or not e:
            raise ValueError("For custom range, both 'start' and 'end' (YYYY-MM-DD) are required.")
        s_d = dt.datetime.strptime(s, "%Y-%m-%d").date()
        e_d = dt.datetime.strptime(e, "%Y-%m-%d").date()
        start = as_utc(s_d)
        end = as_utc(e_d + dt.timedelta(days=1))
    return start, end

def _fetchall(sql: str, args: Tuple[Any, ...]) -> List[Dict[str, Any]]:
    with _get_conn() as conn:
        try:
            cur = conn.cursor(cursor_factory=DictCursor)  # psycopg2
        except Exception:
            cur = conn.cursor()  # psycopg3 dict_row set above
        cur.execute(sql, args)
        rows = cur.fetchall()
        try:
            cols = [d[0] for d in cur.description]
            out = []
            for r in rows:
                if isinstance(r, dict):
                    out.append(r)
                else:
                    out.append({cols[i]: r[i] for i in range(len(cols))})
            return out
        finally:
            cur.close()

def _fetchone(sql: str, args: Tuple[Any, ...]) -> Optional[Dict[str, Any]]:
    rows = _fetchall(sql, args)
    return rows[0] if rows else None

def analytics_data_view(request):
    try:
        start, end = _date_range(request.GET)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

    # KPIs
    kpi_row = _fetchone("""
        SELECT
          COALESCE(SUM(total_price),0) AS revenue,
          COUNT(*) AS orders,
          COALESCE(SUM(CASE WHEN lower(payment_method)='cash' THEN total_price ELSE 0 END),0) AS cash_amount,
          COALESCE(SUM(CASE WHEN lower(payment_method)='online' THEN total_price ELSE 0 END),0) AS online_amount
        FROM public.orders
        WHERE created_at >= %s AND created_at < %s
    """, (start, end)) or {"revenue":0,"orders":0,"cash_amount":0,"online_amount":0}
    orders = int(kpi_row.get("orders") or 0)
    revenue = float(kpi_row.get("revenue") or 0)
    avg_order = (revenue / orders) if orders > 0 else 0.0

    # Table rows
    table_rows = _fetchall("""
        SELECT
          id, order_id, items, total_price, payment_method, order_status, status,
          created_at AT TIME ZONE 'UTC' AS created_at
        FROM public.orders
        WHERE created_at >= %s AND created_at < %s
        ORDER BY created_at DESC
        LIMIT 1000
    """, (start, end))

    for r in table_rows:
        txt = ""
        try:
            arr = json.loads(r.get("items") or "[]")
            names = []
            for it in arr:
                nm = it.get("name")
                q = it.get("quantity", 1)
                names.append(f"{nm} x{q}")
            txt = ", ".join(names)
        except Exception:
            txt = (r.get("items") or "")[:120]
        r["items_text"] = txt

    return JsonResponse({
        "metrics": {
            "totalRevenue": round(revenue, 2),
            "totalOrders": orders,
            "avgOrderValue": round(avg_order, 2),
            "cashAmount": round(float(kpi_row.get("cash_amount") or 0), 2),
            "onlineAmount": round(float(kpi_row.get("online_amount") or 0), 2),
        },
        "table": table_rows
    })

# -------- Chart helpers --------

def _png_html(fig, title="Chart"):
    buf = io.BytesIO()
    fig.tight_layout(pad=0.5)
    fig.savefig(buf, format="png", dpi=140, bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    html = f"""
<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
  html,body{{margin:0;padding:0;background:#fff;height:100%;overflow:hidden}}
  img{{display:block;width:100%;height:100%;object-fit:contain;margin:0}}
</style>
</head><body>
<img alt="{title}" src="data:image/png;base64,{b64}" />
</body></html>
"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")
def chart_view(request, chart_type: str):
    try:
        start, end = _date_range(request.GET)
    except Exception as e:
        return HttpResponse(f"<p>Error: {str(e)}</p>", status=400)

    ct = chart_type.lower()

    if ct == "order-status":
        rows = _fetchall("""
            SELECT COALESCE(NULLIF(TRIM(lower(order_status)),'') , lower(status)) AS s, COUNT(*)::int AS c
            FROM public.orders
            WHERE created_at >= %s AND created_at < %s
            GROUP BY 1
            ORDER BY 2 DESC
        """, (start, end))
        labels = [ (r["s"] or "unknown") for r in rows ]
        sizes = [ r["c"] for r in rows ]
        if not labels:
            labels, sizes = ["no data"], [1]
        fig, ax = plt.subplots(figsize=(8,3.5))
        ax.pie(sizes, labels=labels, autopct="%1.0f%%", startangle=140)
        ax.set_title("Order Status")
        return _png_html(fig, "Order Status")

    elif ct == "top-menu":
        rows = _fetchall("""
            SELECT it->>'name' AS name, SUM(COALESCE((it->>'quantity')::int,1))::int AS qty
            FROM public.orders o
            CROSS JOIN LATERAL jsonb_array_elements(o.items::jsonb) it
            WHERE o.created_at >= %s AND o.created_at < %s
            GROUP BY 1
            ORDER BY qty DESC
            LIMIT 10
        """, (start, end))
        names = [ r["name"] for r in rows ]
        qtys = [ r["qty"] for r in rows ]
        if not names:
            names, qtys = ["no data"], [0]
        fig, ax = plt.subplots(figsize=(8,6))
        ax.barh(names[::-1], qtys[::-1], color="#1e40af")
        ax.set_xlabel("Qty")
        ax.set_title("Top Menu Items")
        return _png_html(fig, "Top Menu Items")

    elif ct == "menu-by-hour":
        rows = _fetchall("""
            SELECT EXTRACT(HOUR FROM created_at)::int AS hr, COUNT(*)::int AS c
            FROM public.orders
            WHERE created_at >= %s AND created_at < %s
            GROUP BY 1
            ORDER BY 1
        """, (start, end))
        counts = { r["hr"]: r["c"] for r in rows }
        xs = list(range(0,24))
        ys = [ counts.get(h,0) for h in xs ]
        fig, ax = plt.subplots(figsize=(8,3.5))
        ax.plot(xs, ys, marker="o", color="#1e40af")
        ax.set_xticks(range(0,24,2))
        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Orders")
        ax.set_title("Orders by Hour (All Menu)")
        return _png_html(fig, "Orders by Hour")

    elif ct == "day-wise-menu":
        # Build stacked bars for top 5 items across days
        day_rows = _fetchall("""
            SELECT date_trunc('day', o.created_at)::date AS day, it->>'name' AS name,
                   SUM(COALESCE((it->>'quantity')::int,1))::int AS qty
            FROM public.orders o
            CROSS JOIN LATERAL jsonb_array_elements(o.items::jsonb) it
            WHERE o.created_at >= %s AND o.created_at < %s
            GROUP BY 1,2
            ORDER BY 1,3 DESC
        """, (start, end))
        # aggregate totals per item to find top 5
        totals = {}
        for r in day_rows:
            nm = r["name"]; totals[nm] = totals.get(nm,0) + int(r["qty"])
        top = [nm for nm,_ in sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:5]]
        # pivot day -> item -> qty
        days = sorted({ r["day"] for r in day_rows })
        series = { nm:[0]*len(days) for nm in top }
        day_idx = { d:i for i,d in enumerate(days) }
        for r in day_rows:
            nm = r["name"]
            if nm in series:
                i = day_idx[r["day"]]
                series[nm][i] += int(r["qty"])
        # if no data
        if not days:
            fig, ax = plt.subplots(figsize=(8,6))
            ax.text(0.5,0.5,"No data", ha="center", va="center")
            ax.axis("off")
            return _png_html(fig, "Day-wise Menu")
        # stacked bars
        fig, ax = plt.subplots(figsize=(8,3.5))
        import numpy as np
        x = np.arange(len(days))
        bottom = np.zeros(len(days))
        colors = ["#1e40af","#059669","#374151","#93c5fd","#a7f3d0"]
        for idx, (nm, vals) in enumerate(series.items()):
            ax.bar(x, vals, bottom=bottom, label=nm, color=colors[idx % len(colors)])
            bottom += np.array(vals)
        ax.set_xticks(x)
        ax.set_xticklabels([d.strftime("%b %d") for d in days], rotation=45, ha="right")
        ax.set_ylabel("Qty")
        ax.set_title("Day-wise Menu (Top 5)")
        ax.legend(fontsize=8, ncols=2)
        return _png_html(fig, "Day-wise Menu")

    elif ct == "day-wise-orders-revenue":
        rows = _fetchall("""
            SELECT date_trunc('day', created_at)::date AS day,
                   COUNT(*)::int AS orders,
                   COALESCE(SUM(total_price),0)::float AS revenue
            FROM public.orders
            WHERE created_at >= %s AND created_at < %s
            GROUP BY 1
            ORDER BY 1
        """, (start, end))
        if not rows:
            fig, ax = plt.subplots(figsize=(8,3.5))
            ax.text(0.5,0.5,"No data", ha="center", va="center")
            ax.axis("off")
            return _png_html(fig, "Day-wise Orders & Revenue")
        days = [ r["day"] for r in rows ]
        orders = [ r["orders"] for r in rows ]
        revenue = [ r["revenue"] for r in rows ]
        fig, ax1 = plt.subplots(figsize=(8,3.5))
        ax1.plot(days, orders, color="#1e40af", marker="o", label="Orders")
        ax1.set_ylabel("Orders", color="#1e40af")
        ax2 = ax1.twinx()
        ax2.plot(days, revenue, color="#059669", marker="s", label="Revenue")
        ax2.set_ylabel("Revenue (₹)", color="#059669")
        ax1.set_title("Day-wise Orders & Revenue")
        fig.autofmt_xdate(rotation=45)
        return _png_html(fig, "Day-wise Orders & Revenue")

    else:
        return HttpResponse(f"<p>Unknown chart type: {chart_type}</p>", status=400)

# Django URL patterns for easy include
urlpatterns = [
    path("data", analytics_data_view, name="analytics-data"),
    path("chart/<str:chart_type>", chart_view, name="analytics-chart"),
]
