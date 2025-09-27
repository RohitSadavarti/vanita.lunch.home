import { useQuery } from "@tanstack/react-query";
import AdminHeader from "@/components/admin-header";
import AdminSidebar from "@/components/admin-sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Clock, IndianRupee, CheckCircle, Utensils } from "lucide-react";
import type { Order } from "@shared/schema";

interface DashboardStats {
  activeOrders: number;
  todayRevenue: number;
  completedOrders: number;
  totalMenuItems: number;
}

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery<DashboardStats>({
    queryKey: ["/api/admin/stats"],
  });

  const { data: recentOrders } = useQuery<Order[]>({
    queryKey: ["/api/admin/orders"],
  });

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <AdminHeader />
      <div className="flex">
        <AdminSidebar currentView="dashboard" />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-card-foreground">Dashboard Overview</h2>
            <p className="text-muted-foreground">Real-time restaurant operations</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Active Orders</p>
                    <p className="text-2xl font-bold text-card-foreground" data-testid="text-active-orders">
                      {stats?.activeOrders || 0}
                    </p>
                  </div>
                  <Clock className="h-8 w-8 text-yellow-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Today's Revenue</p>
                    <p className="text-2xl font-bold text-card-foreground" data-testid="text-revenue">
                      ₹{stats?.todayRevenue || 0}
                    </p>
                  </div>
                  <IndianRupee className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Completed Orders</p>
                    <p className="text-2xl font-bold text-card-foreground" data-testid="text-completed-orders">
                      {stats?.completedOrders || 0}
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Menu Items</p>
                    <p className="text-2xl font-bold text-card-foreground" data-testid="text-menu-items">
                      {stats?.totalMenuItems || 0}
                    </p>
                  </div>
                  <Utensils className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Orders */}
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-card-foreground mb-4">Recent Orders</h3>
              <div className="space-y-3">
                {recentOrders && recentOrders.length > 0 ? (
                  recentOrders.slice(0, 5).map((order: any) => (
                    <div 
                      key={order.id}
                      className="flex items-center justify-between p-3 bg-background rounded-md border border-border"
                      data-testid={`order-card-${order.id}`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold text-sm">
                          #{order.orderNumber}
                        </div>
                        <div>
                          <p className="font-medium text-card-foreground">{order.customerName}</p>
                          <p className="text-sm text-muted-foreground">
                            {JSON.parse(order.items).length} items • ₹{order.totalAmount}
                          </p>
                        </div>
                      </div>
                      <span className={`px-3 py-1 text-xs font-medium rounded-full status-${order.status}`}>
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>No recent orders found</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  );
}
