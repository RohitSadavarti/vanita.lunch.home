# Vanita Lunch Home — Restaurant Order Management System

A full-stack restaurant order management platform for **Vanita Lunch Home**, built with Django (admin portal) and Flask (customer-facing app), backed by PostgreSQL and Firebase Cloud Messaging for real-time order notifications.

---

## Overview

The system consists of two components:

- **OrderMaster** — Django-based admin portal for staff to manage orders, menus, and analytics, with a companion Flutter mobile app
- **vanitalunchhome** — Flask-based customer-facing web app for browsing the menu and placing orders

---

## Features

### Admin Portal (OrderMaster)
- **Session-based authentication** — Mobile + password login with bcrypt hashing
- **Live Order Management** — Kanban-style board with separate columns for Preparing → Ready → Picked Up, with live countdown timers
- **Counter Orders** — Staff can manually place orders for walk-in customers
- **Order Accept / Reject** — Admin can confirm or reject incoming customer orders from a popup modal
- **Menu Management** — Add, edit, and delete menu items with image URLs, categories, and availability
- **Analytics Dashboard** — Revenue, order counts, top menu items, orders by hour, day-wise trends, payment method breakdown, and order source distribution
- **PDF Invoice Generation** — 58mm thermal receipt format, print-ready
- **Firebase Push Notifications** — Real-time new order alerts via FCM topic subscriptions
- **Mobile-Responsive** — Collapsible sidebar, swipe gestures, and touch-optimized layout
- **Custom Management Command** — `create_admin` CLI command to seed admin credentials

### Customer App (vanitalunchhome)
- **WhatsApp OTP Verification** — Registration with 6-digit OTP via Green API
- **Geolocation** — Auto-detect delivery address using browser geolocation + OpenStreetMap reverse geocoding
- **Persistent Cart** — Cart stored in `localStorage`, pre-filled with user details on checkout
- **Order Tracking** — Customers can view their order history and status
- **Email Confirmation** — Optional order confirmation email sent asynchronously

---

## Tech Stack

| Layer | Technology |
|---|---|
| Admin Backend | Python, Django 4.2, Gunicorn |
| Customer Backend | Python, Flask 3.1 |
| Database | PostgreSQL (Supabase) |
| ORM | Django ORM, psycopg2 |
| Auth | bcrypt, Django session-based auth |
| Push Notifications | Firebase Admin SDK (FCM) |
| Analytics Charts | Chart.js, chartjs-plugin-datalabels |
| Frontend | Bootstrap 5, Vanilla JS, Tailwind CSS |
| Static Files | WhiteNoise |
| Deployment | Render (Django), Vercel/Render (Flask) |
| OTP / Messaging | Green API (WhatsApp) |

---

## Project Structure

```
├── OrderMaster/                  # Django admin portal
│   ├── OrderMaster/              # Main Django app
│   │   ├── models.py             # MenuItem, Order, VlhAdmin
│   │   ├── views.py              # All views and API endpoints
│   │   ├── urls.py               # URL routing
│   │   ├── forms.py              # MenuItemForm
│   │   ├── decorators.py         # admin_required decorator
│   │   ├── scripts/
│   │   │   └── analytics_views.py  # Matplotlib-based chart endpoints
│   │   ├── management/commands/
│   │   │   └── create_admin.py   # CLI command to create admin users
│   │   └── templates/OrderMaster/
│   │       ├── base.html         # App shell with sidebar
│   │       ├── dashboard.html
│   │       ├── order_management.html
│   │       ├── menu_management.html
│   │       ├── analytics.html
│   │       ├── take_order.html
│   │       ├── invoice.html
│   │       └── login.html
│   ├── vanita_lunch/             # Django project config
│   │   └── settings.py
│   ├── static/
│   │   ├── css/style.css
│   │   ├── css/management-mobile.css
│   │   └── js/
│   │       ├── firebase-init.js
│   │       └── persistent-popup.js
│   ├── requirements.txt
│   └── build.sh                  # Render build script
│
└── vanitalunchhome/              # Flask customer app
    ├── app.py                    # Main Flask application
    ├── templates/index.html      # Single-page customer UI
    └── static/
        ├── customer.js           # All customer-side JS
        └── landing.css
```

---

## Database Schema

| Table | Description |
|---|---|
| `menu_items` | Menu catalogue (name, price, category, veg/non-veg, image) |
| `orders` | All orders from both customer and counter sources |
| `vlh_admin` | Admin login credentials |
| `vlh_user` | Customer accounts with OTP verification |

### Order Status Flow

```
Customer places order → pending → confirmed (admin accepts) → open (preparing) → ready → pickedup
Counter order          → confirmed                          → open (preparing) → ready → pickedup
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL (or a Supabase project)
- Firebase project with Cloud Messaging enabled

### Django Admin Portal

```bash
cd OrderMaster

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:password@host:port/dbname
export FIREBASE_CREDENTIALS='{"type":"service_account",...}'

# Run migrations
python manage.py migrate

# Create admin user
python manage.py create_admin 9876543210 yourpassword

# Start server
python manage.py runserver
```

### Flask Customer App

```bash
cd vanitalunchhome

pip install -r requirements.txt

export DATABASE_URL=postgresql://user:password@host:port/dbname
export FIREBASE_KEY='{"type":"service_account",...}'
export GREEN_API_ID_INSTANCE=your_instance_id
export GREEN_API_TOKEN=your_token

python app.py
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|---|---|---|
| POST | `/login/` | Admin login (web form or JSON) |
| POST | `/logout/` | Clear session |
| POST | `/api/register` | Customer registration + OTP send |
| POST | `/api/verify-otp` | Verify OTP and activate account |
| POST | `/api/login` | Customer login |

### Orders
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/get-pending-orders/` | Active orders for Flutter app |
| POST | `/api/update-order-status/` | Mark order as ready / picked up |
| POST | `/api/handle-order-action/` | Accept or reject pending customer order |
| POST | `/api/create-manual-order/` | Counter staff place order |
| POST | `/api/place-order/` | Customer place order |
| GET | `/api/all-orders/` | All orders with date filters |
| GET | `/api/customer-orders` | Customer order history by mobile |

### Menu
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/menu-items/` | All menu items |
| GET/POST/PUT | `/api/menu-items/<id>/` | Get, update, or delete a menu item |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/analytics/` | Full analytics data (Django) |
| GET | `/api/analytics-data/` | Completed order analytics |

### Firebase
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/subscribe-topic/` | Subscribe FCM token to `new_orders` topic |

---

## Environment Variables

| Variable | Used By | Description |
|---|---|---|
| `SECRET_KEY` | Django | Django secret key |
| `DATABASE_URL` | Both | PostgreSQL connection string |
| `DEBUG` | Django | Enable debug mode |
| `FIREBASE_CREDENTIALS` | Django | Firebase service account JSON (stringified) |
| `FIREBASE_KEY` | Flask | Firebase service account JSON (stringified) |
| `GREEN_API_ID_INSTANCE` | Flask | Green API WhatsApp instance ID |
| `GREEN_API_TOKEN` | Flask | Green API authentication token |
| `MAIL_USERNAME` | Flask | Gmail address for order confirmations |
| `MAIL_PASSWORD` | Flask | Gmail app password |

---

## Deployment

### Django on Render

The `build.sh` script handles migrations and static file collection automatically on each deploy.

```bash
# build.sh runs:
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py makemigrations OrderMaster
python manage.py migrate
```

Set `DJANGO_SETTINGS_MODULE=vanita_lunch.settings` as a Render environment variable.

---




Application Screenshots

Login Page
The secure entry point for staff members. It utilizes Django's authentication system to ensure only authorized personnel can manage orders and revenue data.
<img width="940" height="564" alt="image" src="https://github.com/user-attachments/assets/76cd45a8-373c-4cbc-b386-0f511ea70e02" />


 


 
Customer Menu (Flutter Mobile)
The main interface where customers browse dishes. It features category filters (Morning Breakfast, Lunch Thali, Veg/Non-Veg) and a dynamic cart system for adding multiple quantities of food items.
<img width="937" height="1204" alt="image" src="https://github.com/user-attachments/assets/208ac8b8-5bac-4c4b-9cc9-8553925e9231" />


 

 
Admin Order Management Dashboard
This is the live "Kitchen Command Center." New orders appear here in real-time. Staff can view the customer’s mobile number, order items, and update the status to "Ready" or "Picked Up."
<img width="940" height="396" alt="image" src="https://github.com/user-attachments/assets/e3184e31-fa8f-4bd8-a5dd-c968b293f80c" />
<img width="940" height="513" alt="image" src="https://github.com/user-attachments/assets/ef28333b-7767-4656-98ba-389499fd2f62" />
<img width="940" height="459" alt="image" src="https://github.com/user-attachments/assets/bb62008a-2644-4df6-ae4f-47c5d4c1f9ce" />
<img width="940" height="564" alt="image" src="https://github.com/user-attachments/assets/ac36c163-acbd-49ad-8d77-9b936132af7e" />
 
 
 

 



Revenue Analytics & Reports
A data-heavy page for the owner. It visualizes daily and monthly sales using charts and tables, allowing for a quick check on the business’s financial health and popular menu items.
<img width="940" height="564" alt="image" src="https://github.com/user-attachments/assets/65853291-c574-4bdc-8bf3-314564127bc0" />
 

Menu & Item Management
The administrative page where the owner can:
•	Add Students/Customers: Maintain user records if needed for credit-based systems.
•	Manage Food Items: Update prices, upload food images, and toggle availability in a flash of time.
•	Bulk Updates: Similar to student data in other systems, the admin can update the teacher/staff schedule or menu items in a single action.
<img width="871" height="1303" alt="image" src="https://github.com/user-attachments/assets/5fbe770f-87b2-4f0c-9010-5acdc82d4550" />
 
 
Digital Invoice
The final output of a successful transaction. It provides a clear breakdown of items, quantities, and the total amount, replacing the need for handwritten bills.
<img width="416" height="690" alt="image" src="https://github.com/user-attachments/assets/0659d1e7-6b5f-45a9-9046-039ae6f7dded" />



  
