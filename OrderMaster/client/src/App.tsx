import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { useAuth } from "@/hooks/useAuth";
import NotFound from "@/pages/not-found";
import AdminLogin from "@/pages/admin-login";
import AdminDashboard from "@/pages/admin-dashboard";
import OrderManagement from "@/pages/order-management";
import MenuManagement from "@/pages/menu-management";
import Analytics from "@/pages/analytics";
import Settings from "@/pages/settings";

// No changes are strictly necessary here if your useAuth hook works correctly,
// but ensure the logic remains: if the user is not authenticated, show the 
// AdminLogin component. The `useAuth` hook will now fail for unauthenticated
// users, which is the correct behavior.
function Router() {
  const { user, isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    // ... loading spinner
  }

  // This logic is now correct. If useAuth returns no user, it shows the login page.
  if (!isAuthenticated || !user?.isAdmin) {
    return <AdminLogin />;
  }

  // ... rest of the router switch
}
  if (!isAuthenticated || !user?.isAdmin) {
    return <AdminLogin />;
  }

  return (
    <Switch>
      <Route path="/" component={AdminDashboard} />
      <Route path="/orders" component={OrderManagement} />
      <Route path="/menu" component={MenuManagement} />
      <Route path="/analytics" component={Analytics} />
      <Route path="/settings" component={Settings} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
