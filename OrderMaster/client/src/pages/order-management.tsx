import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import AdminHeader from "@/components/admin-header";
import AdminSidebar from "@/components/admin-sidebar";
import OrderCard from "@/components/order-card";
import InvoiceModal from "@/components/invoice-modal";
import { useOrders } from "@/hooks/useOrders";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";

export default function OrderManagement() {
  const [activeTab, setActiveTab] = useState<'preparing' | 'ready' | 'completed'>('preparing');
  const [selectedOrder, setSelectedOrder] = useState<any>(null);
  const [showInvoice, setShowInvoice] = useState(false);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: orders = [], isLoading } = useQuery({
    queryKey: ["/api/admin/orders", activeTab],
    queryFn: () => fetch(`/api/admin/orders?status=${activeTab}`).then(res => res.json()),
  });

  const updateOrderStatus = useMutation({
    mutationFn: async ({ orderId, status }: { orderId: string; status: string }) => {
      await apiRequest("PUT", `/api/admin/orders/${orderId}/status`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/orders"] });
      queryClient.invalidateQueries({ queryKey: ["/api/admin/stats"] });
      toast({
        title: "Success",
        description: "Order status updated successfully",
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: "Failed to update order status",
        variant: "destructive",
      });
    },
  });

  const orderCounts = {
    preparing: orders.filter((o: any) => o.status === 'preparing').length,
    ready: orders.filter((o: any) => o.status === 'ready').length,
    completed: orders.filter((o: any) => o.status === 'completed').length,
  };

  const handleMarkReady = (orderId: string) => {
    updateOrderStatus.mutate({ orderId, status: 'ready' });
  };

  const handleMarkCompleted = (orderId: string) => {
    updateOrderStatus.mutate({ orderId, status: 'completed' });
  };

  const handlePrintInvoice = (order: any) => {
    setSelectedOrder(order);
    setShowInvoice(true);
  };

  const handleViewDetails = (order: any) => {
    setSelectedOrder(order);
  };

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
        <AdminSidebar currentView="orders" />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-card-foreground">Order Management</h2>
            <p className="text-muted-foreground">Manage order workflow and status</p>
          </div>

          {/* Order Status Tabs */}
          <div className="border-b border-border mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('preparing')}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'preparing'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
                data-testid="tab-preparing"
              >
                Preparing Orders
                <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs rounded-full px-2 py-1">
                  {orderCounts.preparing}
                </span>
              </button>
              
              <button
                onClick={() => setActiveTab('ready')}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'ready'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
                data-testid="tab-ready"
              >
                Ready Orders
                <span className="ml-2 bg-green-100 text-green-800 text-xs rounded-full px-2 py-1">
                  {orderCounts.ready}
                </span>
              </button>
              
              <button
                onClick={() => setActiveTab('completed')}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === 'completed'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                }`}
                data-testid="tab-completed"
              >
                Completed Orders
                <span className="ml-2 bg-gray-100 text-gray-800 text-xs rounded-full px-2 py-1">
                  {orderCounts.completed}
                </span>
              </button>
            </nav>
          </div>

          {/* Orders Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {orders.length > 0 ? (
              orders.map((order: any) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onMarkReady={handleMarkReady}
                  onMarkCompleted={handleMarkCompleted}
                  onPrintInvoice={handlePrintInvoice}
                  onViewDetails={handleViewDetails}
                />
              ))
            ) : (
              <div className="col-span-2 text-center py-12 text-muted-foreground">
                <p>No {activeTab} orders found</p>
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Invoice Modal */}
      {showInvoice && selectedOrder && (
        <InvoiceModal
          order={selectedOrder}
          onClose={() => setShowInvoice(false)}
        />
      )}
    </div>
  );
}
