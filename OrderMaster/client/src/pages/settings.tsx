import { useState } from "react";
import AdminHeader from "@/components/admin-header";
import AdminSidebar from "@/components/admin-sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";

export default function Settings() {
  const [settings, setSettings] = useState({
    restaurantName: "Vanita Lunch Home",
    contactNumber: "+91 9876543210",
    email: "info@vanitalunchhome.com",
    address: "123 Main Street, City, State",
    newOrderNotifications: true,
    soundAlerts: true,
    emailNotifications: false,
  });

  const { toast } = useToast();

  const handleSaveSettings = () => {
    // TODO: Implement actual settings save
    toast({
      title: "Settings Saved",
      description: "Your settings have been updated successfully.",
    });
  };

  const handleInputChange = (field: string, value: string | boolean) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="min-h-screen bg-background">
      <AdminHeader />
      <div className="flex">
        <AdminSidebar currentView="settings" />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-card-foreground">Settings</h2>
            <p className="text-muted-foreground">Configure restaurant settings</p>
          </div>

          <div className="space-y-6 max-w-2xl">
            {/* Restaurant Information */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Restaurant Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="restaurantName">Restaurant Name</Label>
                    <Input
                      id="restaurantName"
                      value={settings.restaurantName}
                      onChange={(e) => handleInputChange('restaurantName', e.target.value)}
                      data-testid="input-restaurant-name"
                    />
                  </div>
                  <div>
                    <Label htmlFor="contactNumber">Contact Number</Label>
                    <Input
                      id="contactNumber"
                      type="tel"
                      value={settings.contactNumber}
                      onChange={(e) => handleInputChange('contactNumber', e.target.value)}
                      data-testid="input-contact-number"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={settings.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      data-testid="input-email"
                    />
                  </div>
                  <div>
                    <Label htmlFor="address">Address</Label>
                    <Input
                      id="address"
                      value={settings.address}
                      onChange={(e) => handleInputChange('address', e.target.value)}
                      data-testid="input-address"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Notification Settings */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Notification Settings</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="newOrderNotifications">New Order Notifications</Label>
                      <p className="text-sm text-muted-foreground">
                        Receive real-time notifications for new orders
                      </p>
                    </div>
                    <Switch
                      id="newOrderNotifications"
                      checked={settings.newOrderNotifications}
                      onCheckedChange={(checked) => handleInputChange('newOrderNotifications', checked)}
                      data-testid="switch-new-order-notifications"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="soundAlerts">Sound Alerts</Label>
                      <p className="text-sm text-muted-foreground">
                        Play sound when receiving notifications
                      </p>
                    </div>
                    <Switch
                      id="soundAlerts"
                      checked={settings.soundAlerts}
                      onCheckedChange={(checked) => handleInputChange('soundAlerts', checked)}
                      data-testid="switch-sound-alerts"
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <Label htmlFor="emailNotifications">Email Notifications</Label>
                      <p className="text-sm text-muted-foreground">
                        Send order summaries via email
                      </p>
                    </div>
                    <Switch
                      id="emailNotifications"
                      checked={settings.emailNotifications}
                      onCheckedChange={(checked) => handleInputChange('emailNotifications', checked)}
                      data-testid="switch-email-notifications"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Order Management Settings */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Order Management</h3>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="autoMarkReady">Auto-mark Ready Time (minutes)</Label>
                    <Input
                      id="autoMarkReady"
                      type="number"
                      min="0"
                      placeholder="30"
                      className="mt-1"
                      data-testid="input-auto-mark-ready"
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      Automatically mark orders as ready after specified time
                    </p>
                  </div>
                  
                  <div>
                    <Label htmlFor="deliveryRadius">Delivery Radius (km)</Label>
                    <Input
                      id="deliveryRadius"
                      type="number"
                      min="0"
                      step="0.1"
                      placeholder="5.0"
                      className="mt-1"
                      data-testid="input-delivery-radius"
                    />
                    <p className="text-sm text-muted-foreground mt-1">
                      Maximum delivery distance from restaurant
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Save Button */}
            <div className="flex justify-end">
              <Button 
                onClick={handleSaveSettings}
                className="bg-primary text-primary-foreground hover:bg-primary/90"
                data-testid="button-save-settings"
              >
                Save Settings
              </Button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
