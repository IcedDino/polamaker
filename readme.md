# Polamaker

A print-ready polaroid layout generator. Upload your photos, choose a canvas and frame size, and download a 300 DPI PNG ready for any home printer or copy shop.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Vanilla HTML/CSS/JS — single file |
| Backend | Python · FastAPI · Pillow |
| Frontend hosting | Cloudflare Pages |
| Backend hosting | Railway |

## Monorepo structure

```
polamaker/
├── frontend/
│   └── index.html          # Full UI — single self-contained file
├── backend/
│   ├── main.py             # FastAPI app + /api/generate endpoint
│   ├── compositor.py       # Pillow image compositing logic
│   └── requirements.txt
├── worker/
│   ├── index.ts            # Cloudflare Worker — serves HTML, injects API_URL
│   └── wrangler.toml
└── README.md
```

## How it works

1. User picks a canvas (A4, Letter, or custom), polaroid size, and uploads up to 9 photos
2. The frontend sends a `multipart/form-data` POST to `/api/generate` on the Python backend
3. The backend composites the photos into a polaroid layout at 300 DPI using Pillow
4. The frontend receives a PNG blob and offers it as a download

## Local development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

Just open `frontend/index.html` directly in your browser. The `API_URL` variable falls back to `http://localhost:8000` automatically when not served through the Worker.

### Worker (optional locally)

```bash
cd worker
npm install
npx wrangler dev
```

## Environment variables

### Worker (`worker/wrangler.toml`)

```toml
[vars]
API_URL = "https://api.polamaker.floresr.com"
```

### Railway

Set in the Railway dashboard under your service's environment variables:

```
API_URL = https://api.polamaker.floresr.com
```

## Deployment

### Backend → Railway

1. Push repo to GitHub
2. Create a new Railway project, point it at the `backend/` directory
3. Railway auto-detects Python and runs `uvicorn`
4. In Railway → Settings → Custom Domain → add `api.polamaker.floresr.com`
5. Add a CNAME record in your DNS pointing `api.polamaker.floresr.com` to the Railway-provided URL

### Frontend → Cloudflare Workers

1. Connect your GitHub repo to Cloudflare Workers & Pages
2. Set `API_URL` in the Worker's environment variables
3. Point `polamaker.floresr.com` to your Worker via a Cloudflare DNS route
4. Automatic deployments are enabled — every push to `main` redeploys

## API

### `POST /api/generate`

Accepts `multipart/form-data`:

| Field | Type | Description |
|---|---|---|
| `config` | JSON string | Layout configuration (see below) |
| `images` | File(s) | Up to 9 image files (JPG, PNG, WEBP) |

Config shape:

```json
{
  "paper": "a4",
  "orientation": "portrait",
  "polaroid": "tall",
  "custom_w": 8.5,
  "custom_h": 11.0,
  "add_numbers": false
}
```

Returns a `image/png` binary at 300 DPI.

## Polaroid sizes

| Name | Dimensions |
|---|---|
| Tall | 54 × 70 mm — classic portrait |
| Venti | 54 × 62 mm — square format |
| Grande | 70 × 62 mm — wide landscape |
