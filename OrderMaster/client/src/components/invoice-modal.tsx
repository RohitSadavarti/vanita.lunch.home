import { Button } from "@/components/ui/button";
import { X, Printer } from "lucide-react";

interface InvoiceModalProps {
  order: {
    id: string;
    orderNumber: number;
    customerName: string;
    customerMobile: string;
    customerAddress: string;
    totalAmount: string;
    items: string;
    createdAt: string;
  };
  onClose: () => void;
}

export default function InvoiceModal({ order, onClose }: InvoiceModalProps) {
  const items = JSON.parse(order.items);
  const orderDate = new Date(order.createdAt);

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-card rounded-lg shadow-xl p-6 w-full max-w-2xl animate-fade-in">
        <div className="flex items-center justify-between mb-6 no-print">
          <h2 className="text-xl font-bold text-card-foreground">Order Invoice</h2>
          <div className="flex space-x-2">
            <Button
              onClick={handlePrint}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              data-testid="button-print-invoice"
            >
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose} data-testid="button-close-invoice">
              <X className="h-6 w-6" />
            </Button>
          </div>
        </div>
        
        <div className="space-y-4">
          {/* Restaurant Header */}
          <div className="text-center border-b border-border pb-4">
            <h1 className="text-2xl font-bold text-card-foreground">Vanita Lunch Home</h1>
            <p className="text-muted-foreground">Authentic Indian Cuisine</p>
            <p className="text-sm text-muted-foreground">
              Phone: +91 9876543210 | Email: info@vanitalunchhome.com
            </p>
          </div>
          
          {/* Invoice Details */}
          <div className="grid grid-cols-2 gap-4 text-sm border-b border-border pb-4">
            <div>
              <h3 className="font-semibold text-card-foreground mb-2">Bill To:</h3>
              <p className="text-muted-foreground">{order.customerName}</p>
              <p className="text-muted-foreground">{order.customerMobile}</p>
              <p className="text-muted-foreground text-xs">{order.customerAddress}</p>
            </div>
            <div className="text-right">
              <p><span className="font-medium">Invoice #:</span> INV-{order.orderNumber}</p>
              <p><span className="font-medium">Date:</span> {orderDate.toLocaleDateString()}</p>
              <p><span className="font-medium">Time:</span> {orderDate.toLocaleTimeString()}</p>
            </div>
          </div>
          
          {/* Order Items Table */}
          <div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2">Item</th>
                  <th className="text-center py-2">Qty</th>
                  <th className="text-right py-2">Price</th>
                  <th className="text-right py-2">Total</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item: any, index: number) => (
                  <tr key={index} className="border-b border-border">
                    <td className="py-2">{item.name}</td>
                    <td className="text-center py-2">{item.quantity}</td>
                    <td className="text-right py-2">₹{item.price}</td>
                    <td className="text-right py-2">₹{item.price * item.quantity}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-semibold">
                  <td colSpan={3} className="text-right py-2">Total Amount:</td>
                  <td className="text-right py-2">₹{order.totalAmount}</td>
                </tr>
              </tfoot>
            </table>
          </div>
          
          {/* Footer */}
          <div className="text-center text-sm text-muted-foreground mt-6 border-t border-border pt-4">
            <p>Thank you for your order!</p>
            <p>Enjoy your meal from Vanita Lunch Home</p>
          </div>
        </div>
      </div>
    </div>
  );
}
