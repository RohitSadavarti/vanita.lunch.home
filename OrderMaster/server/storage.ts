import {
  users,
  menuItems,
  orders,
  orderItems,
  type User,
  type UpsertUser,
  type MenuItem,
  type InsertMenuItem,
  type Order,
  type InsertOrder,
  type OrderItem,
  type InsertOrderItem,
} from "@shared/schema";
import { db } from "./db";
import { eq, desc, and, like, sql } from "drizzle-orm";

export interface IStorage {
  // User operations (required for Replit Auth)
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;
  
  // Menu operations
  getMenuItems(): Promise<MenuItem[]>;
  getMenuItem(id: string): Promise<MenuItem | undefined>;
  createMenuItem(item: InsertMenuItem): Promise<MenuItem>;
  updateMenuItem(id: string, item: Partial<InsertMenuItem>): Promise<MenuItem>;
  deleteMenuItem(id: string): Promise<void>;
  searchMenuItems(query: string, category?: string): Promise<MenuItem[]>;
  
  // Order operations
  getOrders(): Promise<Order[]>;
  getOrder(id: string): Promise<Order | undefined>;
  createOrder(order: InsertOrder, items: InsertOrderItem[]): Promise<Order>;
  updateOrderStatus(id: string, status: string): Promise<Order>;
  getOrdersByStatus(status: string): Promise<Order[]>;
  getOrderStats(): Promise<{
    activeOrders: number;
    todayRevenue: number;
    completedOrders: number;
    totalMenuItems: number;
  }>;
  
  // Order items operations
  getOrderItems(orderId: string): Promise<OrderItem[]>;
}

export class DatabaseStorage implements IStorage {
  // User operations
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }
  // Add this method inside the DatabaseStorage class in storage.ts

  async getAdminByMobile(mobile: string): Promise<VlhAdmin | undefined> {
    const [admin] = await db
      .select()
      .from(vlhAdmin)
      .where(eq(vlhAdmin.mobile, mobile));
    return admin;
  }
  // Add this method inside the DatabaseStorage class in storage.ts
  async verifyPassword(password: string, hash: string): Promise<boolean> {
    // This is a simplified check. PostgreSQL's crypt() is not directly available
    // in Node.js. This line simulates the check.
    // For a real app, you MUST use a library like bcryptjs to compare hashes.
    const [result] = await db.execute(sql`SELECT '${sql.raw(password)}' = crypt('${sql.raw(password)}', '${sql.raw(hash)}') as is_valid`);
    return (result as any)?.is_valid === true;
  }

  async upsertUser(userData: UpsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(userData)
      .onConflictDoUpdate({
        target: users.id,
        set: {
          ...userData,
          updatedAt: new Date(),
        },
      })
      .returning();
    return user;
  }

  // Menu operations
  async getMenuItems(): Promise<MenuItem[]> {
    return await db.select().from(menuItems).orderBy(desc(menuItems.createdAt));
  }

  async getMenuItem(id: string): Promise<MenuItem | undefined> {
    const [item] = await db.select().from(menuItems).where(eq(menuItems.id, id));
    return item;
  }

  async createMenuItem(item: InsertMenuItem): Promise<MenuItem> {
    const [menuItem] = await db.insert(menuItems).values(item).returning();
    return menuItem;
  }

  async updateMenuItem(id: string, item: Partial<InsertMenuItem>): Promise<MenuItem> {
    const [menuItem] = await db
      .update(menuItems)
      .set({ ...item, updatedAt: new Date() })
      .where(eq(menuItems.id, id))
      .returning();
    return menuItem;
  }

  async deleteMenuItem(id: string): Promise<void> {
    await db.delete(menuItems).where(eq(menuItems.id, id));
  }

  async searchMenuItems(query: string, category?: string): Promise<MenuItem[]> {
    let whereClause = like(menuItems.name, `%${query}%`);
    
    if (category) {
      whereClause = and(whereClause, eq(menuItems.category, category)) as any;
    }
    
    return await db.select().from(menuItems).where(whereClause);
  }

  // Order operations
  async getOrders(): Promise<Order[]> {
    return await db.select().from(orders).orderBy(desc(orders.createdAt));
  }

  async getOrder(id: string): Promise<Order | undefined> {
    const [order] = await db.select().from(orders).where(eq(orders.id, id));
    return order;
  }

  async createOrder(order: InsertOrder, items: InsertOrderItem[]): Promise<Order> {
    const orderNumber = await this.getNextOrderNumber();
    
    const [createdOrder] = await db
      .insert(orders)
      .values({ ...order, orderNumber })
      .returning();

    // Create order items
    const orderItemsWithOrderId = items.map(item => ({
      ...item,
      orderId: createdOrder.id,
    }));
    
    await db.insert(orderItems).values(orderItemsWithOrderId);
    
    return createdOrder;
  }

  async updateOrderStatus(id: string, status: string): Promise<Order> {
    const [order] = await db
      .update(orders)
      .set({ status, updatedAt: new Date() })
      .where(eq(orders.id, id))
      .returning();
    return order;
  }

  async getOrdersByStatus(status: string): Promise<Order[]> {
    return await db
      .select()
      .from(orders)
      .where(eq(orders.status, status))
      .orderBy(desc(orders.createdAt));
  }

  async getOrderStats(): Promise<{
    activeOrders: number;
    todayRevenue: number;
    completedOrders: number;
    totalMenuItems: number;
  }> {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const [activeOrdersResult] = await db
      .select({ count: sql<number>`count(*)` })
      .from(orders)
      .where(eq(orders.status, 'preparing'));
    
    const [todayRevenueResult] = await db
      .select({ total: sql<number>`sum(total_amount)` })
      .from(orders)
      .where(
        and(
          sql`date(created_at) = date(${today})`,
          eq(orders.status, 'completed')
        )
      );
    
    const [completedOrdersResult] = await db
      .select({ count: sql<number>`count(*)` })
      .from(orders)
      .where(
        and(
          sql`date(created_at) = date(${today})`,
          eq(orders.status, 'completed')
        )
      );
    
    const [menuItemsResult] = await db
      .select({ count: sql<number>`count(*)` })
      .from(menuItems)
      .where(eq(menuItems.isAvailable, true));

    return {
      activeOrders: activeOrdersResult.count || 0,
      todayRevenue: todayRevenueResult.total || 0,
      completedOrders: completedOrdersResult.count || 0,
      totalMenuItems: menuItemsResult.count || 0,
    };
  }

  async getOrderItems(orderId: string): Promise<OrderItem[]> {
    return await db.select().from(orderItems).where(eq(orderItems.orderId, orderId));
  }

  private async getNextOrderNumber(): Promise<number> {
    const [lastOrder] = await db
      .select({ orderNumber: orders.orderNumber })
      .from(orders)
      .orderBy(desc(orders.orderNumber))
      .limit(1);
    
    return (lastOrder?.orderNumber || 100) + 1;
  }
}

export const storage = new DatabaseStorage();
