import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth";
import { insertMenuItemSchema, insertOrderSchema } from "@shared/schema";
import multer from "multer";
import path from "path";
import fs from "fs";

// Configure multer for file uploads
const upload = multer({
  dest: 'uploads/',
  limits: { fileSize: 5 * 1024 * 1024 }, // 5MB limit
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (mimetype && extname) {
      return cb(null, true);
    } else {
      cb(new Error('Only image files are allowed'));
    }
  }
});

// Store WebSocket connections for real-time notifications
const adminConnections = new Set<WebSocket>();

export async function registerRoutes(app: Express): Promise<Server> {
  // Auth middleware
  await setupAuth(app);

  // Serve uploaded files
  app.use('/uploads', (req, res, next) => {
    // Basic security check for file access
    const filename = path.basename(req.path);
    const filepath = path.join(process.cwd(), 'uploads', filename);
    
    if (fs.existsSync(filepath)) {
      res.sendFile(filepath);
    } else {
      res.status(404).json({ message: 'File not found' });
    }
  });

  // Auth routes
app.get('/api/auth/user', isAuthenticated, async (req: any, res) => {
  try {
    // Since we removed Replit auth, req.user is undefined.
    // We will return a mock admin user to allow the frontend to load.
    // In a real application, you would replace this with a proper user session check.
    const mockAdminUser = {
      id: 'mock-admin-user',
      email: 'admin@example.com',
      firstName: 'Admin',
      lastName: 'User',
      profileImageUrl: '',
      isAdmin: true, // This is important for the frontend logic
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    res.json(mockAdminUser);
  } catch (error) {
    console.error("Error fetching user:", error);
    res.status(500).json({ message: "Failed to fetch user" });
  }
});
  // Admin check middleware
  const isAdmin = async (req: any, res: any, next: any) => {
    try {
      const userId = req.user.claims.sub;
      const user = await storage.getUser(userId);
      
      if (!user || !user.isAdmin) {
        return res.status(403).json({ message: "Admin access required" });
      }
      
      next();
    } catch (error) {
      res.status(500).json({ message: "Failed to verify admin status" });
    }
  };

  // Menu management routes
  app.get('/api/admin/menu', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const menuItems = await storage.getMenuItems();
      res.json(menuItems);
    } catch (error) {
      console.error("Error fetching menu items:", error);
      res.status(500).json({ message: "Failed to fetch menu items" });
    }
  });

  app.post('/api/admin/menu', isAuthenticated, isAdmin, upload.single('image'), async (req, res) => {
    try {
      const validation = insertMenuItemSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid menu item data", errors: validation.error.errors });
      }

      let imageUrl = null;
      if (req.file) {
        // In production, you'd upload to a cloud storage service
        imageUrl = `/uploads/${req.file.filename}`;
      }

      const menuItem = await storage.createMenuItem({
        ...validation.data,
        imageUrl,
      });

      // Notify all admin clients about new menu item
      broadcastToAdmins({
        type: 'MENU_ITEM_ADDED',
        data: menuItem
      });

      res.json(menuItem);
    } catch (error) {
      console.error("Error creating menu item:", error);
      res.status(500).json({ message: "Failed to create menu item" });
    }
  });

  app.put('/api/admin/menu/:id', isAuthenticated, isAdmin, upload.single('image'), async (req, res) => {
    try {
      const { id } = req.params;
      const validation = insertMenuItemSchema.partial().safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid menu item data", errors: validation.error.errors });
      }

      let updateData = validation.data;
      if (req.file) {
        updateData.imageUrl = `/uploads/${req.file.filename}`;
      }

      const menuItem = await storage.updateMenuItem(id, updateData);
      res.json(menuItem);
    } catch (error) {
      console.error("Error updating menu item:", error);
      res.status(500).json({ message: "Failed to update menu item" });
    }
  });

  app.delete('/api/admin/menu/:id', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      await storage.deleteMenuItem(id);
      res.json({ message: "Menu item deleted successfully" });
    } catch (error) {
      console.error("Error deleting menu item:", error);
      res.status(500).json({ message: "Failed to delete menu item" });
    }
  });

  // Order management routes
  app.get('/api/admin/orders', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const { status } = req.query;
      let orders;
      
      if (status && typeof status === 'string') {
        orders = await storage.getOrdersByStatus(status);
      } else {
        orders = await storage.getOrders();
      }
      
      res.json(orders);
    } catch (error) {
      console.error("Error fetching orders:", error);
      res.status(500).json({ message: "Failed to fetch orders" });
    }
  });

  app.get('/api/admin/orders/:id', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      const order = await storage.getOrder(id);
      
      if (!order) {
        return res.status(404).json({ message: "Order not found" });
      }
      
      const orderItems = await storage.getOrderItems(id);
      res.json({ ...order, orderItems });
    } catch (error) {
      console.error("Error fetching order:", error);
      res.status(500).json({ message: "Failed to fetch order" });
    }
  });

  app.put('/api/admin/orders/:id/status', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const { id } = req.params;
      const { status } = req.body;
      
      if (!['preparing', 'ready', 'completed'].includes(status)) {
        return res.status(400).json({ message: "Invalid order status" });
      }
      
      const order = await storage.updateOrderStatus(id, status);
      
      // Notify all admin clients about order status change
      broadcastToAdmins({
        type: 'ORDER_STATUS_UPDATED',
        data: order
      });
      
      res.json(order);
    } catch (error) {
      console.error("Error updating order status:", error);
      res.status(500).json({ message: "Failed to update order status" });
    }
  });

  // Customer order creation (for when customers place orders)
  app.post('/api/orders', async (req, res) => {
    try {
      const validation = insertOrderSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid order data", errors: validation.error.errors });
      }

      const { items, ...orderData } = req.body;
      const order = await storage.createOrder(orderData, items);
      
      // Notify all admin clients about new order
      broadcastToAdmins({
        type: 'NEW_ORDER',
        data: order
      });
      
      res.json(order);
    } catch (error) {
      console.error("Error creating order:", error);
      res.status(500).json({ message: "Failed to create order" });
    }
  });

  // Dashboard stats
  app.get('/api/admin/stats', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const stats = await storage.getOrderStats();
      res.json(stats);
    } catch (error) {
      console.error("Error fetching stats:", error);
      res.status(500).json({ message: "Failed to fetch stats" });
    }
  });

  // Public menu endpoint for customer portal
  app.get('/api/menu', async (req, res) => {
    try {
      const { search, category } = req.query;
      let menuItems;
      
      if (search && typeof search === 'string') {
        menuItems = await storage.searchMenuItems(search, category as string);
      } else {
        menuItems = await storage.getMenuItems();
        if (category && typeof category === 'string') {
          menuItems = menuItems.filter(item => item.category === category);
        }
      }
      
      // Only return available items for customers
      menuItems = menuItems.filter(item => item.isAvailable);
      res.json(menuItems);
    } catch (error) {
      console.error("Error fetching public menu:", error);
      res.status(500).json({ message: "Failed to fetch menu" });
    }
  });

  const httpServer = createServer(app);

  // WebSocket server for real-time admin notifications
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws: WebSocket, req) => {
    console.log('New WebSocket connection');
    
    // Add to admin connections
    adminConnections.add(ws);
    
    // Send connection status
    ws.send(JSON.stringify({
      type: 'CONNECTION_STATUS',
      data: { status: 'connected' }
    }));

    ws.on('close', () => {
      console.log('WebSocket connection closed');
      adminConnections.delete(ws);
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
      adminConnections.delete(ws);
    });
  });

  function broadcastToAdmins(message: any) {
    const messageString = JSON.stringify(message);
    adminConnections.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(messageString);
      }
    });
  }

  return httpServer;
}
