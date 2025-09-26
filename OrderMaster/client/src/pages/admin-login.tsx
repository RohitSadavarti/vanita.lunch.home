import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function AdminLogin() {
  const { toast } = useToast();

  useEffect(() => {
    // Show unauthorized message if needed
    toast({
      title: "Admin Access Required",
      description: "Please log in with your admin account to access the portal.",
      variant: "default",
    });
  }, [toast]);

  const handleLogin = () => {
    // Redirect to Replit OAuth login
    window.location.href = "/api/login";
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md animate-fade-in">
        <CardContent className="pt-8 pb-8">
          <div className="text-center mb-6">
            <ShieldCheck className="h-12 w-12 text-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-card-foreground">Admin Portal</h2>
            <p className="text-muted-foreground mt-2">Access the restaurant management system</p>
          </div>
          
          <div className="space-y-4">
            <div className="text-center text-sm text-muted-foreground">
              <p>Only authorized administrators can access this portal.</p>
              <p className="mt-2">Please log in with your admin account.</p>
            </div>
            
            <Button 
              onClick={handleLogin}
              className="w-full bg-primary text-primary-foreground font-semibold py-3 hover:bg-primary/90 transition-colors"
              data-testid="button-admin-login"
            >
              Login as Admin
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
