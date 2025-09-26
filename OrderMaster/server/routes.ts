import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { setupAuth, isAuthenticated } from "./replitAuth"; // still using this for session setup
import { insertMenuItemSchema, insertOrderSchema } from "@shared/schema";
import multer from "multer";
import path from "path";
import fs from "fs";
import bcrypt from "bcryptjs";

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
  // Auth/session setup
  await setupAuth(app);

  // Serve uploaded files
  app.use('/uploads', (req, res) => {
    const filename = path.basename(req.path);
    const filepath = path.join(process.cwd(), 'uploads', filename);
    
    if (fs.existsSync(filepath)) {
      res.sendFile(filepath);
    } else {
      res.status(404).json({ message: 'File not found' });
    }
  });

  /**
   * 🔹 NEW: Login endpoint
   */
  app.post('/api/login', async (req, res) => {
  const { mobile, password } = req.body;

  if (!mobile || !password) {
    return res.status(400).json({ message: 'Mobile and password are required' });
  }

  try {
    const admin = await storage.getAdminByMobile(mobile);

    if (!admin) {
      // Use a generic message to prevent user enumeration
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Use bcryptjs to securely compare the password with the hash from the DB
    const isValid = bcrypt.compareSync(password, admin.passwordHash);
    
    if (!isValid) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // If valid, create a session
    req.session.user = { id: admin.id, mobile: admin.mobile, isAdmin: true };
    req.session.save();

    return res.status(200).json({ message: 'Login successful' });

  } catch (error) {
    console.error("Login error:", error);
    return res.status(500).json({ message: "Internal server error" });
  }
});

  /**
   * 🔹 NEW: Logout endpoint
   */
  app.post('/api/logout', (req: any, res) => {
    req.session.destroy((err: any) => {
      if (err) {
        return res.status(500).json({ message: 'Could not log out.' });
      }
      res.clearCookie('connect.sid');
      return res.status(200).json({ message: 'Logout successful' });
    });
  });

  /**
   * 🔹 UPDATED: Auth user endpoint
   */
  app.get('/api/auth/user', (req: any, res) => {
    if (req.session.user && req.session.user.isAdmin) {
      res.json(req.session.user);
    } else {
      res.status(401).json({ message: 'Unauthorized' });
    }
  });

  // Admin check middleware (now uses session)
  const isAdmin = async (req: any, res: any, next: any) => {
    try {
      if (!req.session.user || !req.session.user.isAdmin) {
        return res.status(403).json({ message: "Admin access required" });
      }
      next();
    } catch (error) {
      res.status(500).json({ message: "Failed to verify admin status" });
    }
  };

  /**
   * 🔹 Admin menu management routes
   */
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
        imageUrl = `/uploads/${req.file.filename}`;
      }

      const menuItem = await storage.createMenuItem({
        ...validation.data,
        imageUrl,
      });

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

  /**
   * 🔹 Order management
   */
  app.get('/api/admin/orders', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const { status } = req.query;
      const orders = status && typeof status === 'string'
        ? await storage.getOrdersByStatus(status)
        : await storage.getOrders();
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
      if (!order) return res.status(404).json({ message: "Order not found" });

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
      broadcastToAdmins({ type: 'ORDER_STATUS_UPDATED', data: order });

      res.json(order);
    } catch (error) {
      console.error("Error updating order status:", error);
      res.status(500).json({ message: "Failed to update order status" });
    }
  });

  /**
   * 🔹 Customer order creation
   */
  app.post('/api/orders', async (req, res) => {
    try {
      const validation = insertOrderSchema.safeParse(req.body);
      if (!validation.success) {
        return res.status(400).json({ message: "Invalid order data", errors: validation.error.errors });
      }

      const { items, ...orderData } = req.body;
      const order = await storage.createOrder(orderData, items);

      broadcastToAdmins({ type: 'NEW_ORDER', data: order });
      res.json(order);
    } catch (error) {
      console.error("Error creating order:", error);
      res.status(500).json({ message: "Failed to create order" });
    }
  });

  /**
   * 🔹 Dashboard stats
   */
  app.get('/api/admin/stats', isAuthenticated, isAdmin, async (req, res) => {
    try {
      const stats = await storage.getOrderStats();
      res.json(stats);
    } catch (error) {
      console.error("Error fetching stats:", error);
      res.status(500).json({ message: "Failed to fetch stats" });
    }
  });

  /**
   * 🔹 Public menu
   */
  app.get('/api/menu', async (req, res) => {
    try {
      const { search, category } = req.query;
      let menuItems = search && typeof search === 'string'
        ? await storage.searchMenuItems(search, category as string)
        : await storage.getMenuItems();

      if (category && typeof category === 'string') {
        menuItems = menuItems.filter(item => item.category === category);
      }

      res.json(menuItems.filter(item => item.isAvailable));
    } catch (error) {
      console.error("Error fetching public menu:", error);
      res.status(500).json({ message: "Failed to fetch menu" });
    }
  });

  /**
   * 🔹 WebSockets for real-time notifications
   */
  const httpServer = createServer(app);
  const wss = new WebSocketServer({ server: httpServer, path: '/ws' });

  wss.on('connection', (ws: WebSocket) => {
    console.log('New WebSocket connection');
    adminConnections.add(ws);

    ws.send(JSON.stringify({
      type: 'CONNECTION_STATUS',
      data: { status: 'connected' }
    }));

    ws.on('close', () => {
      console.log('WebSocket closed');
      adminConnections.delete(ws);
    });

    ws.on('error', (error) => {
      console.error('WebSocket error:', error);
      adminConnections.delete(ws);
    });
  });

  function broadcastToAdmins(message: any) {
    const str = JSON.stringify(message);
    adminConnections.forEach(ws => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(str);
      }
    });
  }

  return httpServer;
}
