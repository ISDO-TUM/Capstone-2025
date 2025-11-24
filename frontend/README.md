# Capstone Frontend

React 19 + TypeScript + Vite + TailwindCSS frontend for the Capstone 2025 project.

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite 7** - Build tool and dev server
- **TailwindCSS 3** - Utility-first CSS
- **React Router** - Client-side routing
- **TanStack Query** - Server state management

## Getting Started

```bash
# Install dependencies
npm install

# Start dev server (runs on http://localhost:5173)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable components
│   ├── pages/          # Page components
│   ├── lib/            # Utilities
│   ├── types/          # TypeScript types
│   └── App.tsx         # Root component
├── public/             # Static assets
└── index.html          # HTML entry point
```

## Development

The dev server proxies API requests to `http://localhost:5000` (configured in `vite.config.ts`).

## Migration Status

See `FRONTEND_MIGRATION_PLAN.md` in the project root for the complete migration plan.
