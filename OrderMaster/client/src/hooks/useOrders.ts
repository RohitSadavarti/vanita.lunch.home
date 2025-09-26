import { useQuery } from "@tanstack/react-query";

export function useOrders(status?: string) {
  return useQuery({
    queryKey: status ? ["/api/admin/orders", status] : ["/api/admin/orders"],
    queryFn: () => {
      const url = status ? `/api/admin/orders?status=${status}` : "/api/admin/orders";
      return fetch(url).then(res => res.json());
    },
  });
}

export function useOrderStats() {
  return useQuery({
    queryKey: ["/api/admin/stats"],
  });
}
