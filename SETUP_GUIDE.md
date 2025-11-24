# Environment Variables Setup Guide

## Quick Answer

**For local development with Docker, you need:**

1. **HOSTNAME** = `localhost` (for local development)
2. **DB_USER** = `user` (default - you can keep this)
3. **DB_PASSWORD** = `password` (default - you can keep this)
4. **DB_NAME** = `papers` (default - you can keep this)

---

## Detailed Explanation

### 1. HOSTNAME

**What it is:** The domain where your frontend application is accessible. Used by Clerk for authentication.

**For local development:**
```
HOSTNAME=localhost
```

**For production:**
```
HOSTNAME=yourdomain.com
```

**Where to find it:** 
- This is just the domain name where your app runs
- For local dev: `localhost` (without port number)
- For production: Your actual domain (e.g., `myapp.com`)

---

### 2. Database Variables (DB_USER, DB_PASSWORD, DB_NAME)

**What they are:** PostgreSQL database connection credentials.

**Default values (work fine for local development):**
```
DB_USER=user
DB_PASSWORD=password
DB_NAME=papers
DB_PORT=5432
```

**Where to find them:**
- These are **created by Docker** when you first run `docker compose up`
- You can use the defaults above, or set custom values
- If you change them, make sure they match in your `.env` file

**Note:** These are only used when connecting to a remote database. For Docker, the database is created automatically with these credentials.

---

### 3. Clerk Keys (You already know these)

- `CLERK_SECRET_KEY` - From Clerk Dashboard → API Keys
- `CLERK_PUBLISHABLE_KEY` - From Clerk Dashboard → API Keys  
- `CLERK_FRONTEND_API_URL` - From Clerk Dashboard → Frontend API URL

---

### 4. OpenAI API Key (You already know this)

- `OPENAI_API_KEY` - From https://platform.openai.com/api-keys

---

## Complete .env File Template

```env
# OpenAI
OPENAI_API_KEY=sk-your-actual-key-here

# Clerk
CLERK_SECRET_KEY=sk_test_your-actual-key-here
CLERK_PUBLISHABLE_KEY=pk_test_your-actual-key-here
CLERK_FRONTEND_API_URL=https://your-instance.clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js

# Hostname (for local dev)
HOSTNAME=localhost

# Database (defaults - you can keep these)
DB_USER=user
DB_PASSWORD=password
DB_NAME=papers
DB_PORT=5432
```

---

## Next Steps

1. **Edit `.env` file** and fill in:
   - Your OpenAI API key
   - Your Clerk keys
   - Set `HOSTNAME=localhost`
   - Keep DB defaults (or customize if you want)

2. **Start Docker:**
   ```bash
   docker compose up -d
   ```

3. **Start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

4. **Check if backend is running:**
   ```bash
   docker compose logs web
   ```

---

## Troubleshooting

**If you get authentication errors:**
- Make sure `HOSTNAME` matches where your frontend is accessible
- For local dev: use `localhost` (not `localhost:5173`)

**If you get database errors:**
- Make sure Docker containers are running: `docker compose ps`
- Check database logs: `docker compose logs db`

**If backend returns 500 errors:**
- Check backend logs: `docker compose logs web`
- Verify all environment variables are set correctly


