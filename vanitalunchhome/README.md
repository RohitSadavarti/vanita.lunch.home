# Full-Stack Restaurant Ordering System

This is a complete, real-time ordering system for a restaurant, built with a Next.js frontend and a Python Flask backend. It's designed to be deployed directly from a GitHub repository.

## ✨ Features

- **Customer View:** Browse the menu, add items to a cart, and place an order for cash pickup.
- **Admin Dashboard:** A real-time view of incoming orders, separated into "Preparing" and "Ready" columns.
- **Real-time Updates:** New orders instantly appear on the admin screen with a sound notification, powered by WebSockets.
- **Scalable Backend:** A robust Flask API for managing menu items and orders.
- **PostgreSQL Database:** Securely stores all application data.

## 🚀 Deployment Guide

### 1. Backend Deployment (e.g., on Render)

1.  **Push to GitHub:** Make sure your `backend` code is in a GitHub repository.
2.  **Create a New Web Service on Render:** Connect your GitHub account and select the repository.
3.  **Settings:**
    -   **Environment:** Python 3
    -   **Build Command:** `pip install -r requirements.txt && flask db upgrade`
    -   **Start Command:** `gunicorn run:app`
4.  **Environment Variables:** Add your `DATABASE_URL` and `SECRET_KEY` in the Render dashboard.
5.  **Deploy!** Render will build and deploy your Flask app. Copy the public URL (e.g., `https://your-backend.onrender.com`).

### 2. Frontend Deployment (on Vercel)

1.  **Push to GitHub:** The `frontend` code should be in the same repository.
2.  **Create a New Project on Vercel:** Import your GitHub repository.
3.  **Configure Project:**
    -   Vercel will automatically detect that it's a Next.js project.
    -   Set the **Root Directory** to `frontend`.
4.  **Environment Variables:** Add `NEXT_PUBLIC_API_URL` and set its value to your deployed backend URL from Render.
5.  **Deploy!** Vercel will build and deploy your Next.js frontend.

### 3. Local Development

**Running the Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Set up your .env file
flask db upgrade
flask run
```

**Running the Frontend:**
```bash
cd frontend
npm install
# Set up your .env.local file
npm run dev
```
