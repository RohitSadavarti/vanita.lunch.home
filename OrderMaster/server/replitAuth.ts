import type { Express, RequestHandler } from "express";
import session from "express-session";
import connectPg from "connect-pg-simple";

// The Replit-specific imports are no longer needed, so they can be removed or commented out.
// import * as client from "openid-client";
// import { Strategy, type VerifyFunction } from "openid-client/passport";
// import passport from "passport";
// import memoize from "memoizee";
// import { storage } from "./storage";

export function getSession() {
  const sessionTtl = 7 * 24 * 60 * 60 * 1000; // 1 week
  const PgStore = connectPg(session);
  const sessionStore = new PgStore({
    conString: process.env.DATABASE_URL,
    createTableIfMissing: false,
    ttl: sessionTtl,
    tableName: "sessions",
  });
  return session({
    secret: process.env.SESSION_SECRET!,
    store: sessionStore,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      // In production, you'll want secure: true, but that requires HTTPS
      secure: process.env.NODE_ENV === "production", 
      maxAge: sessionTtl,
    },
  });
}

export async function setupAuth(app: Express) {
  // We still set up session management, as it's good practice.
  app.set("trust proxy", 1);
  app.use(getSession());

  // All Replit-specific passport and OIDC strategy setup is removed.
  // This means the /api/login and /api/callback routes will no longer function,
  // but they are not needed if we are bypassing authentication.
}

/**
 * This middleware function is modified to bypass authentication.
 * For a production app, you should replace this with a real
 * authentication check (e.g., username/password, or another OAuth provider).
 */
export const isAuthenticated: RequestHandler = async (req, res, next) => {
  // This function now immediately allows the request to proceed.
  return next();
};
