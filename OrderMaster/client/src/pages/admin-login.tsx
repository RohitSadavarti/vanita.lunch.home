import { useState } from "react";
import { useLocation } from "wouter";
import { ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";

export default function AdminLogin() {
  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const { toast } = useToast();
  const [, navigate] = useLocation();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mobile, password }),
    });

    if (response.ok) {
      toast({
        title: "Login Successful",
        description: "Welcome to the Admin Portal.",
      });
      // Navigate to the dashboard on successful login
      navigate("/");
      // You might need to trigger a re-fetch of user data here
      window.location.reload(); // Simple way to force a reload
    } else {
      toast({
        title: "Login Failed",
        description: "Invalid mobile number or password.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md animate-fade-in">
        <CardContent className="pt-8 pb-8">
          <div className="text-center mb-6">
            <ShieldCheck className="h-12 w-12 text-primary mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-card-foreground">Admin Portal</h2>
            <p className="text-muted-foreground mt-2">Please sign in to continue</p>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <Label htmlFor="mobile">Mobile Number</Label>
              <Input
                id="mobile"
                type="tel"
                value={mobile}
                onChange={(e) => setMobile(e.target.value)}
                required
                placeholder="Enter your 10-digit mobile number"
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
              />
            </div>
            <Button 
              type="submit"
              className="w-full bg-primary text-primary-foreground font-semibold py-3 hover:bg-primary/90 transition-colors"
            >
              Sign In
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
