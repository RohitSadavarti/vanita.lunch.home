import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, Truck, Eye, Printer } from "lucide-react";

interface OrderCardProps {
  order: {
    id: string;
    orderNumber: number;
    customerName: string;
    customerMobile: string;
    status: string;
    totalAmount: string;
    items: string;
    createdAt: string;
  };
  onMarkReady: (orderId: string) => void;
  onMarkCompleted: (orderId: string) => void;
  onPrintInvoice: (order: any) => void;
  onViewDetails: (order: any) => void;
}

export default function OrderCard({
  order,
  onMarkReady,
  onMarkCompleted,
  onPrintInvoice,
  onViewDetails,
}: OrderCardProps) {
  const items = JSON.parse(order.items);
  const timeAgo = getTimeAgo(order.createdAt);

  function getTimeAgo(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return "Just now";
    if (diffInMinutes < 60) return `${diffInMinutes} min ago`;
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours}h ago`;
    
    return date.toLocaleDateString();
  }

  return (
    <Card className="animate-fade-in" data-testid={`order-card-${order.id}`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold ${
              order.status === 'preparing' ? 'bg-yellow-100 text-yellow-800' :
              order.status === 'ready' ? 'bg-green-100 text-green-800' :
              'bg-gray-100 text-gray-800'
            }`}>
              #{order.orderNumber}
            </div>
            <div>
              <h3 className="font-semibold text-card-foreground">{order.customerName}</h3>
              <p className="text-sm text-muted-foreground">{order.customerMobile}</p>
              <p className="text-xs text-muted-foreground">{timeAgo}</p>
            </div>
          </div>
          <span className={`px-3 py-1 text-xs font-medium rounded-full status-${order.status}`}>
            {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
          </span>
        </div>
        
        <div className="space-y-2 mb-4">
          {items.map((item: any, index: number) => (
            <div key={index} className="flex justify-between text-sm">
              <span>{item.name} x{item.quantity}</span>
              <span>₹{item.price * item.quantity}</span>
            </div>
          ))}
        </div>

        <div className="border-t border-border pt-4 mb-4">
          <div className="flex justify-between font-semibold">
            <span>Total</span>
            <span>₹{order.totalAmount}</span>
          </div>
        </div>

        <div className="flex space-x-2">
          {order.status === 'preparing' && (
            <Button
              onClick={() => onMarkReady(order.id)}
              className="flex-1 bg-green-500 text-white hover:bg-green-600"
              data-testid={`button-mark-ready-${order.id}`}
            >
              <Check className="h-4 w-4 mr-2" />
              Mark Ready
            </Button>
          )}
          
          {order.status === 'ready' && (
            <Button
              onClick={() => onMarkCompleted(order.id)}
              className="flex-1 bg-blue-500 text-white hover:bg-blue-600"
              data-testid={`button-mark-completed-${order.id}`}
            >
              <Truck className="h-4 w-4 mr-2" />
              Delivered
            </Button>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDetails(order)}
            data-testid={`button-view-details-${order.id}`}
          >
            <Eye className="h-4 w-4" />
          </Button>
          
          {(order.status === 'ready' || order.status === 'completed') && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPrintInvoice(order)}
              data-testid={`button-print-invoice-${order.id}`}
            >
              <Printer className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
