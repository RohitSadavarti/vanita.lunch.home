import { useState, useEffect } from "react";
import { UtensilsCrossed, BellRing, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function AdminHeader() {
  const [hasNewNotification, setHasNewNotification] = useState(false);
  const { connectionStatus, lastMessage } = useWebSocket();

  useEffect(() => {
    if (lastMessage?.type === 'NEW_ORDER') {
      setHasNewNotification(true);
      // Auto-hide notification after 5 seconds
      setTimeout(() => setHasNewNotification(false), 5000);
    }
  }, [lastMessage]);

  const handleLogout = () => {
    window.location.href = "/api/logout";
  };

  return (
    <header className="bg-card border-b border-border sticky top-0 z-40">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-4">
          <UtensilsCrossed className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-xl font-bold text-card-foreground">Vanita Lunch Home</h1>
            <p className="text-sm text-muted-foreground">Admin Portal</p>
          </div>
        </div>
        
        {/* Real-time Status Indicators */}
        <div className="flex items-center space-x-4">
          {/* WebSocket Connection Status */}
          <div className="flex items-center space-x-2">
            <div 
              className={`w-3 h-3 rounded-full ${
                connectionStatus === 'connected' 
                  ? 'bg-green-500 animate-pulse' 
                  : 'bg-red-500'
              }`}
              data-testid={`status-${connectionStatus}`}
            />
            <span className="text-sm text-muted-foreground capitalize">
              {connectionStatus}
            </span>
          </div>
          
          {/* New Order Notification */}
          {hasNewNotification && (
            <div className="relative p-2 bg-red-100 text-red-800 rounded-lg animate-pulse-notification">
              <BellRing className="h-5 w-5" />
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full"></span>
            </div>
          )}
          
          {/* Admin Profile */}
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center font-semibold">
              A
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleLogout}
              className="text-muted-foreground hover:text-foreground"
              data-testid="button-logout"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
