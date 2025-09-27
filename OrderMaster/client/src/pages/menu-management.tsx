import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import AdminHeader from "@/components/admin-header";
import AdminSidebar from "@/components/admin-sidebar";
import MenuItemForm from "@/components/menu-item-form";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Edit, Trash2, Search } from "lucide-react";
import { apiRequest } from "@/lib/queryClient";
import { useToast } from "@/hooks/use-toast";
import type { MenuItem } from "@shared/schema";

export default function MenuManagement() {
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: menuItems = [], isLoading } = useQuery<MenuItem[]>({
    queryKey: ["/api/admin/menu"],
  });

  const deleteMenuItem = useMutation({
    mutationFn: async (itemId: string) => {
      await apiRequest("DELETE", `/api/admin/menu/${itemId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/menu"] });
      toast({
        title: "Success",
        description: "Menu item deleted successfully",
      });
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to delete menu item",
        variant: "destructive",
      });
    },
  });

  const filteredItems = menuItems.filter((item: any) => {
    const matchesSearch = item.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !categoryFilter || item.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleDeleteItem = (itemId: string) => {
    if (confirm("Are you sure you want to delete this menu item?")) {
      deleteMenuItem.mutate(itemId);
    }
  };

  const handleEditItem = (item: any) => {
    setEditingItem(item);
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
        <AdminSidebar currentView="menu" />
        <main className="flex-1 p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-card-foreground">Menu Management</h2>
            <p className="text-muted-foreground">Add, edit, and manage menu items</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Add Menu Item Form */}
            <div className="lg:col-span-1">
              <MenuItemForm
                editingItem={editingItem}
                onCancel={() => setEditingItem(null)}
                onSuccess={() => setEditingItem(null)}
              />
            </div>

            {/* Menu Items List */}
            <div className="lg:col-span-2">
              <Card>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-card-foreground">Current Menu Items</h3>
                    <div className="flex items-center space-x-2">
                      <div className="relative">
                        <Input
                          type="text"
                          placeholder="Search menu items..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          className="w-64 pl-10"
                          data-testid="input-menu-search"
                        />
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                      </div>
                      
                      <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                        <SelectTrigger className="w-48" data-testid="select-category-filter">
                          <SelectValue placeholder="All Categories" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="">All Categories</SelectItem>
                          <SelectItem value="breakfast">Breakfast</SelectItem>
                          <SelectItem value="lunch">Lunch</SelectItem>
                          <SelectItem value="dinner">Dinner</SelectItem>
                          <SelectItem value="snacks">Snacks</SelectItem>
                          <SelectItem value="beverages">Beverages</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {filteredItems.length > 0 ? (
                      filteredItems.map((item: any) => (
                        <div
                          key={item.id}
                          className="flex items-center space-x-4 p-4 border border-border rounded-lg hover:bg-accent/50 transition-colors"
                          data-testid={`menu-item-${item.id}`}
                        >
                          {item.imageUrl && (
                            <img
                              src={item.imageUrl}
                              alt={item.name}
                              className="w-16 h-16 object-cover rounded-md"
                            />
                          )}
                          {!item.imageUrl && (
                            <div className="w-16 h-16 bg-muted rounded-md flex items-center justify-center">
                              <span className="text-muted-foreground text-xs">No Image</span>
                            </div>
                          )}
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-semibold text-card-foreground">{item.name}</h4>
                              <span className={`w-3 h-3 rounded-sm ${item.type === 'veg' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                            </div>
                            <p className="text-sm text-muted-foreground">{item.description}</p>
                            <div className="flex items-center space-x-4 mt-1">
                              <span className="text-sm font-medium text-primary">₹{item.price}</span>
                              <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                                {item.category}
                              </span>
                              {!item.isAvailable && (
                                <span className="text-xs px-2 py-1 bg-red-100 text-red-800 rounded-full">
                                  Unavailable
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex space-x-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleEditItem(item)}
                              data-testid={`button-edit-${item.id}`}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDeleteItem(item.id)}
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              data-testid={`button-delete-${item.id}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-12 text-muted-foreground">
                        <p>No menu items found</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
