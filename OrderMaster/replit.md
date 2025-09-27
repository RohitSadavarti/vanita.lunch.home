# Replit Configuration for Vanita Lunch Order Management System

## Overview

Vanita Lunch is a Django-based restaurant order management system designed for staff to handle menu items and track orders. The application provides an admin interface for managing menu items (with categories, pricing, and images) and monitoring order status through different stages - from preparation to completion. It features user authentication, CRUD operations for menu management, and real-time order status updates through AJAX calls.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Django 4.2+**: Chosen as the main web framework for rapid development, built-in admin interface, and robust ORM capabilities
- **Python**: Primary programming language providing excellent ecosystem for web development
- **Model-View-Template (MVT) Pattern**: Standard Django architecture separating data models, business logic, and presentation layers

### Database Design
- **PostgreSQL**: Production database using psycopg2-binary adapter for reliability and ACID compliance
- **Django ORM**: Database abstraction layer handling migrations and queries
- **Two main models**:
  - `MenuItem`: Stores menu items with categories, pricing, dietary preferences, and images
  - `Order`: Tracks order lifecycle with status transitions (preparing → ready → completed)

### Frontend Architecture
- **Server-side Rendered Templates**: Django template engine for dynamic HTML generation
- **Bootstrap 5**: CSS framework for responsive design and consistent UI components
- **Vanilla JavaScript**: Client-side functionality for AJAX order status updates without framework overhead
- **Static File Handling**: Separate CSS/JS files with Django's static file system

### Authentication & Authorization
- **Django's Built-in Authentication**: Session-based authentication for admin users
- **Login Required Decorators**: Protecting admin views from unauthorized access
- **CSRF Protection**: Built-in Django middleware for form security

### File Upload System
- **Pillow Integration**: Image processing library for menu item photos
- **Media File Handling**: Django's file upload system with configurable storage paths
- **Image Optimization**: Automatic handling of different image formats for menu items

### Configuration Management
- **python-decouple**: Environment variable management for sensitive settings
- **Environment-based Configuration**: Separate settings for development/production environments
- **Debug Mode Controls**: Configurable debug settings based on environment

### Deployment Architecture
- **Gunicorn WSGI Server**: Production-ready Python WSGI HTTP server
- **Static File Serving**: Configured for both development and production environments
- **Database Connection Pooling**: PostgreSQL connection management through psycopg2

## External Dependencies

### Core Framework Dependencies
- **Django (4.2+)**: Web framework providing MVC architecture, ORM, admin interface, and security features
- **psycopg2-binary**: PostgreSQL database adapter for Python/Django integration

### Media & File Processing
- **Pillow**: Python Imaging Library for handling menu item image uploads, resizing, and format conversion

### Configuration & Environment
- **python-decouple**: Environment variable management for secure configuration of database credentials, secret keys, and environment-specific settings

### Production Deployment
- **Gunicorn**: WSGI HTTP server for serving Django applications in production environments

### Frontend Libraries (CDN)
- **Bootstrap 5.1.3**: CSS framework for responsive design, component styling, and grid system
- **Bootstrap JavaScript Bundle**: Interactive components and utilities for enhanced user experience

### Development Tools
- **Django Development Server**: Built-in server for local development and testing
- **Django Admin Interface**: Automatic admin panel generation for model management
- **Django Static Files Handler**: Development static file serving and collection system