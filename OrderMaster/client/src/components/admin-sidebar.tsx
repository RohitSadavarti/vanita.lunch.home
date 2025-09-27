import { Link, useLocation } from "wouter";
import { 
  LayoutDashboard, 
  ClipboardList, 
  Menu, 
  BarChart3, 
  Settings 
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AdminSidebarProps {
  currentView: string;
}

export default function AdminSidebar({ currentView }: AdminSidebarProps) {
  const [location] = useLocation();

  const navItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      href: "/",
    },
    {
      id: "orders",
      label: "Order Management",
      icon: ClipboardList,
      href: "/orders",
    },
    {
      id: "menu",
      label: "Menu Management",
      icon: Menu,
      href: "/menu",
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: BarChart3,
      href: "/analytics",
    },
    {
      id: "settings",
      label: "Settings",
      icon: Settings,
      href: "/settings",
    },
  ];

  return (
    <aside className="w-64 bg-card border-r border-border min-h-screen">
      <nav className="p-4">
        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location === item.href || currentView === item.id;
            
            return (
              <Link key={item.id} href={item.href}>
                <div
                  className={cn(
                    "sidebar-nav flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors cursor-pointer",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                  )}
                  data-testid={`nav-${item.id}`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                  {item.id === "orders" && (
                    <span className="ml-auto bg-red-500 text-white text-xs rounded-full px-2 py-1 hidden">
                      0
                    </span>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      </nav>
    </aside>
  );
}
