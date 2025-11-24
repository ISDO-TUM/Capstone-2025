# Application Startup Guide

## Quick Start

### 1. Start Docker Containers
```bash
docker compose up -d
```

This starts:
- **PostgreSQL** database on port `5432`
- **ChromaDB** vector database on port `8000`
- **Flask backend** on port `80`

### 2. Start Frontend Development Server
```bash
cd frontend
npm run dev
```

This starts the React frontend on `http://localhost:5173`

### 3. Verify Everything is Running

**Check Docker containers:**
```bash
docker compose ps
```

All containers should show `Up` status.

**Check backend logs:**
```bash
docker compose logs web --tail 20
```

You should see: `* Running on http://127.0.0.1:80`

**Check if backend is accessible:**
- Open browser: `http://localhost:80`
- Or test API: The frontend should automatically proxy to `http://localhost:80/api/*`

---

## Environment Variables

Make sure your `.env` file has all required variables:

```env
# Required
OPENAI_API_KEY=your_key_here
CLERK_SECRET_KEY=your_key_here
CLERK_PUBLISHABLE_KEY=your_key_here
CLERK_FRONTEND_API_URL=your_url_here
HOSTNAME=localhost

# Database (defaults work fine)
DB_USER=user
DB_PASSWORD=password
DB_NAME=papers
DB_PORT=5432
```

---

## Troubleshooting

### Backend not starting?
1. Check logs: `docker compose logs web`
2. Rebuild container: `docker compose up -d --build web`
3. Verify environment variables are set in `.env`

### Frontend can't connect to backend?
1. Make sure Docker containers are running: `docker compose ps`
2. Check Vite proxy in `frontend/vite.config.ts` points to `http://localhost:80`
3. Check browser console for errors

### Port 80 already in use?
- On Windows, port 80 might be used by IIS or other services
- Change port in `docker-compose.yml` (line 38) to something else like `8080:80`
- Update `frontend/vite.config.ts` proxy target accordingly

### Database connection errors?
- Make sure PostgreSQL container is running: `docker compose ps`
- Check database logs: `docker compose logs db`
- Verify `.env` has correct DB credentials

---

## First Time Setup

1. **Create `.env` file** (copy from `.env.example` if it exists)
2. **Fill in your API keys** (OpenAI, Clerk)
3. **Start Docker:** `docker compose up -d`
4. **Wait for containers to be ready** (~30 seconds)
5. **Start frontend:** `cd frontend && npm run dev`
6. **Open browser:** `http://localhost:5173`

---

## Stopping the Application

**Stop Docker containers:**
```bash
docker compose down
```

**Stop frontend:**
Press `Ctrl+C` in the terminal running `npm run dev`

---

## Restarting After Changes

**Backend changes:**
```bash
docker compose restart web
```

**Frontend changes:**
- Vite automatically reloads on file changes
- If needed, restart: `Ctrl+C` then `npm run dev` again

**Full restart:**
```bash
docker compose down
docker compose up -d
cd frontend && npm run dev
```

