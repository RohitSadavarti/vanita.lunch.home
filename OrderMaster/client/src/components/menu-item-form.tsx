import { useState, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Upload, Plus, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface MenuItemFormProps {
  editingItem?: any;
  onCancel?: () => void;
  onSuccess?: () => void;
}

export default function MenuItemForm({ editingItem, onCancel, onSuccess }: MenuItemFormProps) {
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    price: "",
    category: "",
    type: "",
    isAvailable: true,
  });
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  
  const { toast } = useToast();
  const queryClient = useQueryClient();

  useEffect(() => {
    if (editingItem) {
      setFormData({
        name: editingItem.name || "",
        description: editingItem.description || "",
        price: editingItem.price || "",
        category: editingItem.category || "",
        type: editingItem.type || "",
        isAvailable: editingItem.isAvailable ?? true,
      });
      
      if (editingItem.imageUrl) {
        setImagePreview(editingItem.imageUrl);
      }
    } else {
      setFormData({
        name: "",
        description: "",
        price: "",
        category: "",
        type: "",
        isAvailable: true,
      });
      setImagePreview("");
      setImageFile(null);
    }
  }, [editingItem]);

  const createMenuItem = useMutation({
    mutationFn: async (formDataToSend: FormData) => {
      const response = await fetch("/api/admin/menu", {
        method: "POST",
        body: formDataToSend,
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Failed to create menu item");
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/menu"] });
      toast({
        title: "Success",
        description: "Menu item created successfully",
      });
      resetForm();
      onSuccess?.();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to create menu item",
        variant: "destructive",
      });
    },
  });

  const updateMenuItem = useMutation({
    mutationFn: async (formDataToSend: FormData) => {
      const response = await fetch(`/api/admin/menu/${editingItem.id}`, {
        method: "PUT",
        body: formDataToSend,
        credentials: "include",
      });
      
      if (!response.ok) {
        throw new Error("Failed to update menu item");
      }
      
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["/api/admin/menu"] });
      toast({
        title: "Success",
        description: "Menu item updated successfully",
      });
      resetForm();
      onSuccess?.();
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to update menu item",
        variant: "destructive",
      });
    },
  });

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      price: "",
      category: "",
      type: "",
      isAvailable: true,
    });
    setImageFile(null);
    setImagePreview("");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const formDataToSend = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value.toString());
    });

    if (imageFile) {
      formDataToSend.append("image", imageFile);
    }

    if (editingItem) {
      updateMenuItem.mutate(formDataToSend);
    } else {
      createMenuItem.mutate(formDataToSend);
    }
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setImageFile(null);
    setImagePreview("");
  };

  return (
    <Card className="sticky top-6">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-card-foreground">
            {editingItem ? "Edit Menu Item" : "Add New Menu Item"}
          </h3>
          {editingItem && onCancel && (
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="itemName">Item Name</Label>
            <Input
              id="itemName"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              required
              data-testid="input-item-name"
            />
          </div>
          
          <div>
            <Label htmlFor="itemDescription">Description</Label>
            <Textarea
              id="itemDescription"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
              required
              data-testid="textarea-item-description"
            />
          </div>
          
          <div>
            <Label htmlFor="itemPrice">Price (₹)</Label>
            <Input
              id="itemPrice"
              type="number"
              step="0.01"
              min="0"
              value={formData.price}
              onChange={(e) => setFormData(prev => ({ ...prev, price: e.target.value }))}
              required
              data-testid="input-item-price"
            />
          </div>
          
          <div>
            <Label htmlFor="itemCategory">Category</Label>
            <Select
              value={formData.category}
              onValueChange={(value) => setFormData(prev => ({ ...prev, category: value }))}
            >
              <SelectTrigger data-testid="select-item-category">
                <SelectValue placeholder="Select Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="breakfast">Breakfast</SelectItem>
                <SelectItem value="lunch">Lunch</SelectItem>
                <SelectItem value="dinner">Dinner</SelectItem>
                <SelectItem value="snacks">Snacks</SelectItem>
                <SelectItem value="beverages">Beverages</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label htmlFor="itemType">Type</Label>
            <Select
              value={formData.type}
              onValueChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
            >
              <SelectTrigger data-testid="select-item-type">
                <SelectValue placeholder="Select Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="veg">Vegetarian</SelectItem>
                <SelectItem value="non-veg">Non-Vegetarian</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div>
            <Label>Upload Image</Label>
            <div className="border-2 border-dashed border-border rounded-lg p-4 text-center">
              <input
                type="file"
                accept="image/*"
                onChange={handleImageChange}
                className="hidden"
                id="itemImage"
                data-testid="input-item-image"
              />
              
              {!imagePreview ? (
                <label
                  htmlFor="itemImage"
                  className="flex flex-col items-center space-y-2 text-muted-foreground hover:text-foreground cursor-pointer"
                >
                  <Upload className="h-8 w-8" />
                  <span className="text-sm">Click to upload image</span>
                </label>
              ) : (
                <div className="space-y-2">
                  <img
                    src={imagePreview}
                    alt="Preview"
                    className="mx-auto rounded-md image-preview"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={removeImage}
                    className="text-red-500 hover:text-red-700"
                    data-testid="button-remove-image"
                  >
                    Remove Image
                  </Button>
                </div>
              )}
            </div>
          </div>
          
          <Button
            type="submit"
            className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
            disabled={createMenuItem.isPending || updateMenuItem.isPending}
            data-testid="button-submit-menu-item"
          >
            {editingItem ? (
              updateMenuItem.isPending ? "Updating..." : "Update Menu Item"
            ) : (
              createMenuItem.isPending ? "Adding..." : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Menu Item
                </>
              )
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
