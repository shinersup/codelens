# CodeLens Frontend

React + Vite frontend for the CodeLens AI code review platform.

## Stack

- **React 18** with React Router v6
- **Tailwind CSS** — dark terminal-inspired theme
- **Axios** — API client with JWT interceptors
- **Lucide React** — icons
- **Framer Motion** — animations (optional progressive enhancement)

## Setup

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` requests to `http://localhost:8000` (the FastAPI backend).

## Pages

| Route | Page | Auth Required |
|-------|------|---------------|
| `/` | Landing page | No |
| `/login` | Sign in | No |
| `/register` | Create account | No |
| `/analyze` | Code review/explain/refactor | Yes |
| `/history` | Past reviews | Yes |

## API Integration

All API calls go through `src/utils/api.js` which maps to the FastAPI backend:

- `POST /api/auth/register` — register
- `POST /api/auth/login` — login (returns JWT)
- `POST /api/review` — AI code review
- `POST /api/explain` — AI code explanation
- `POST /api/refactor` — AI refactor suggestions
- `GET /api/history` — user's past reviews

## Environment Variables

```
VITE_API_URL=     # Leave empty for Vite proxy (dev), or set full URL for production
```

## Build

```bash
npm run build     # outputs to dist/
npm run preview   # preview production build locally
```
