# Restaurant Management System

## Overview

This is a full-stack restaurant management system built for "Vanita Lunch Home" with both customer-facing and admin functionalities. The system features a React frontend with TypeScript, an Express.js backend, and PostgreSQL database with Drizzle ORM. The architecture supports real-time order management, menu administration, and customer ordering capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The client-side application is built using React with TypeScript and follows a component-based architecture:

- **UI Framework**: React 18 with functional components and hooks
- **Styling**: Tailwind CSS with shadcn/ui component library for consistent design
- **State Management**: TanStack Query (React Query) for server state and caching
- **Routing**: Wouter for lightweight client-side routing
- **Real-time Communication**: WebSocket connection for live order updates
- **Build Tool**: Vite for fast development and optimized production builds

The frontend is structured with separate pages for different admin functions (dashboard, orders, menu, analytics, settings) and uses a sidebar navigation pattern. Components are organized into reusable UI elements and feature-specific components.

### Backend Architecture
The server-side follows an Express.js REST API pattern with TypeScript:

- **Framework**: Express.js with TypeScript for type safety
- **API Design**: RESTful endpoints organized by feature (auth, menu, orders, admin)
- **Real-time Features**: WebSocket server for live order notifications to admin users
- **File Handling**: Multer middleware for menu item image uploads
- **Session Management**: Express sessions with PostgreSQL storage
- **Error Handling**: Centralized error middleware with proper HTTP status codes

The backend uses a storage abstraction pattern to separate database operations from route handlers, making the code more maintainable and testable.

### Database Architecture
PostgreSQL database with Drizzle ORM for type-safe database operations:

- **ORM**: Drizzle ORM providing full TypeScript support and SQL-like syntax
- **Schema Design**: Relational tables for users, menu items, orders, and order items
- **Session Storage**: Database-backed session storage for authentication persistence
- **Migrations**: Drizzle Kit for database schema management and migrations

Key database relationships include:
- Users table for admin authentication and authorization
- Menu items with categories, pricing, and availability status
- Orders linked to order items for detailed order tracking
- Session storage for maintaining user authentication state

### Authentication and Authorization
Replit-based OAuth authentication system:

- **OAuth Provider**: Replit OAuth for secure user authentication
- **Session Management**: Server-side sessions stored in PostgreSQL
- **Authorization**: Role-based access control with admin flag in user records
- **Security**: Passport.js integration for OAuth flow handling

The system distinguishes between regular users and admin users, with admin-only routes protected by middleware that checks the user's admin status.

### Real-time Features
WebSocket implementation for live updates:

- **Order Notifications**: Real-time alerts to admin dashboard when new orders arrive
- **Connection Management**: Automatic reconnection handling for network interruptions
- **Status Updates**: Live order status changes broadcast to connected admin clients

### File Management
Image upload and serving system:

- **Upload Handling**: Multer middleware with file type validation and size limits
- **Storage**: Local file system storage in uploads directory
- **Serving**: Static file serving with security checks for uploaded images
- **Validation**: File type restrictions to only allow image formats

## External Dependencies

### Database Services
- **Neon Database**: PostgreSQL hosting service via `@neondatabase/serverless`
- **Connection Pooling**: Built-in connection management for serverless environments

### Authentication Services
- **Replit OAuth**: OAuth provider for user authentication and authorization
- **OpenID Connect**: Standard OAuth 2.0 / OpenID Connect implementation

### UI and Styling
- **Radix UI**: Accessible component primitives for complex UI elements
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Lucide Icons**: Icon library for consistent iconography throughout the app

### Development and Build Tools
- **Vite**: Fast build tool and development server
- **TypeScript**: Static type checking for both frontend and backend
- **ESBuild**: Fast JavaScript bundler for production builds
- **Replit Plugins**: Development tools including error overlay and dev banner

### File Upload and Processing
- **Multer**: Middleware for handling multipart/form-data file uploads
- **File Type Validation**: Image format restrictions for menu item photos

### Real-time Communication
- **WebSocket (ws)**: Native WebSocket implementation for real-time features
- **Connection Management**: Automatic reconnection and connection status tracking

### State Management and Data Fetching
- **TanStack Query**: Server state management, caching, and synchronization
- **React Hook Form**: Form handling with validation support
- **Zod**: Schema validation for form inputs and API data