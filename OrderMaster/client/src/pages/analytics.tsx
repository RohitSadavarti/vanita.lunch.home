import AdminHeader from "@/components/admin-header";
import AdminSidebar from "@/components/admin-sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { BarChart } from "lucide-react";

export default function Analytics() {
  // Mock data for popular items
  const popularItems = [
    { name: "Dal Tadka", orders: 45 },
    { name: "Paneer Butter Masala", orders: 38 },
    { name: "Butter Roti", orders: 67 },
    { name: "Jeera Rice", orders: 29 },
    { name: "Mixed Vegetable", orders: 24 },
  ];

  return (
    <div className="min-h-screen bg-background">
      <AdminHeader />
      <div className="flex">
        <AdminSidebar currentView="analytics" />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-card-foreground">Analytics Dashboard</h2>
            <p className="text-muted-foreground">Restaurant performance insights</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Sales Chart Placeholder */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Daily Sales Trend</h3>
                <div className="h-64 flex items-center justify-center text-muted-foreground">
                  <div className="text-center">
                    <BarChart className="h-12 w-12 mx-auto mb-2" />
                    <p>Sales chart will be displayed here</p>
                    <p className="text-sm mt-1">Integrate with Chart.js or similar library</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Popular Items */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Popular Menu Items</h3>
                <div className="space-y-3">
                  {popularItems.map((item, index) => (
                    <div 
                      key={item.name}
                      className="flex items-center justify-between p-3 bg-background rounded-md border border-border"
                      data-testid={`popular-item-${index}`}
                    >
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-medium text-muted-foreground">
                          #{index + 1}
                        </span>
                        <span className="text-card-foreground">{item.name}</span>
                      </div>
                      <span className="text-muted-foreground">{item.orders} orders</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Revenue Breakdown */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Revenue Breakdown</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Today</span>
                    <span className="font-medium">₹5,240</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">This Week</span>
                    <span className="font-medium">₹32,580</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">This Month</span>
                    <span className="font-medium">₹1,25,600</span>
                  </div>
                  <div className="border-t pt-2 mt-4">
                    <div className="flex justify-between font-semibold">
                      <span>Average Order Value</span>
                      <span>₹385</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Order Status Distribution */}
            <Card>
              <CardContent className="p-6">
                <h3 className="text-lg font-semibold text-card-foreground mb-4">Order Distribution</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Preparing</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 h-2 bg-yellow-200 rounded-full">
                        <div className="w-3/4 h-2 bg-yellow-500 rounded-full"></div>
                      </div>
                      <span className="text-sm">12</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Ready</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 h-2 bg-green-200 rounded-full">
                        <div className="w-1/4 h-2 bg-green-500 rounded-full"></div>
                      </div>
                      <span className="text-sm">4</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Completed</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-20 h-2 bg-gray-200 rounded-full">
                        <div className="w-full h-2 bg-gray-500 rounded-full"></div>
                      </div>
                      <span className="text-sm">38</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </div>
  );
}
