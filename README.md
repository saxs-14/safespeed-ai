# SafeSpeed AI

AI-powered road safety MVP: upload traffic footage and it detects vehicles, tracks them
across frames, and estimates their speed — flagging vehicles over a configurable limit.

## Problem statement

Speeding contributes heavily to road accidents. Schools, private estates, fleet operators
and municipalities often have cameras but no way to turn that footage into actionable
speed data without expensive radar hardware or manual review.

## Solution

Upload a video (or run the bundled demo clip) and SafeSpeed AI runs it through a
detection → tracking → speed-estimation pipeline, then shows a live dashboard of
vehicle counts, average/max speed and speeding events, with CSV export for reporting.

## Features

- Vehicle detection (car, bus, motorbike, bicycle) via OpenCV DNN + MobileNet-SSD
- Multi-object tracking across frames (lightweight centroid tracker)
- Speed estimation from pixel displacement, using a configurable calibration
- Configurable speed limit and overspeed flagging
- Evidence crop saved per detected vehicle
- Dashboard: total vehicles, average/max speed, speeding count, event history
- CSV export of all events
- Demo mode that requires no camera or uploaded footage

## Architecture

```text
frontend (React/Vite/TS/Tailwind)  ->  backend (FastAPI)  ->  SQLite
                                              |
                                     OpenCV DNN (MobileNet-SSD)
                                     + centroid tracker
                                     + speed estimator
```

## Technology stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, OpenCV (DNN module)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
- **Detection model**: MobileNet-SSD (Caffe, VOC-trained, ~23MB) — chosen over
  YOLO/Ultralytics specifically to avoid a multi-GB PyTorch/CUDA dependency chain,
  keeping the MVP installable on constrained hardware
- **Containerization**: Docker + docker-compose

## Folder structure

```text
safespeed-ai/
├── backend/
│   ├── app/            # FastAPI app, routers, detection pipeline
│   ├── models/          # MobileNet-SSD prototxt + caffemodel (fetch script below)
│   ├── demo/            # Demo video + generator script
│   ├── tests/            # pytest suite
│   └── requirements.txt
├── frontend/
│   └── src/              # Landing page + dashboard
├── docker-compose.yml
└── README.md
```

## Installation

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env
```

The MobileNet-SSD model files must exist at `backend/models/MobileNetSSD_deploy.prototxt`
and `backend/models/MobileNetSSD_deploy.caffemodel`. If missing, fetch them:

```bash
curl -L -o models/MobileNetSSD_deploy.prototxt https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.prototxt
curl -L -o models/MobileNetSSD_deploy.caffemodel https://raw.githubusercontent.com/djmv/MobilNet_SSD_opencv/master/MobileNetSSD_deploy.caffemodel
```

### Frontend

```bash
cd frontend
npm install
```

## Environment variables

See `backend/.env.example`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite connection string |
| `DEFAULT_SPEED_LIMIT_KMH` | Default speed limit applied to new sessions |
| `DEFAULT_PIXELS_PER_METER` | Default calibration factor |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `UPLOAD_DIR` | Where uploaded videos + evidence crops are stored |
| `MAX_UPLOAD_MB` | Upload size limit |

## Running locally

```bash
# Terminal 1
cd backend && venv\Scripts\activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173. API docs at http://localhost:8000/docs.

### Docker

```bash
docker compose up --build
```

## Demo instructions

1. Open the dashboard and click **Run demo mode** — no upload required.
2. The bundled clip (`backend/demo/traffic-demo.mp4`) is a **synthetic composite**: a
   real car photo (Wikimedia Commons, CC-licensed) moving across a real road photo at a
   known pixel velocity, regenerable via `python demo/generate_demo_video.py`. It exists
   because publicly available "top-down traffic cam" footage turned out to be a poor
   match for this lightweight detector (see Limitations) — a controlled clip with a
   known ground-truth speed is a more honest way to demonstrate (and unit-test) the
   pipeline than an unverified found video.
3. To test with your own footage, use the upload form instead — a normal, roughly
   eye-level or moderately elevated view of moving vehicles works best (see Limitations).

## API documentation

Interactive docs at `/docs` (Swagger UI). Key endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/analyze` | Upload + analyze a video (`file`, `speed_limit_kmh`, `pixels_per_meter`) |
| POST | `/api/analyze/demo` | Run analysis on the bundled demo clip |
| GET | `/api/events` | List speed events (filter by `session_id`, `speeding_only`) |
| GET | `/api/events/export` | CSV export |
| GET | `/api/dashboard/summary` | Aggregate KPIs |

## Database

SQLite (`safespeed.db`), two tables: `analysis_sessions` (one row per processed video)
and `speed_events` (one row per tracked vehicle). Swap `DATABASE_URL` for a Postgres DSN
to move to Postgres — SQLAlchemy handles both without code changes.

## Security considerations

- **API key required on every endpoint except `/api/health`.** Set `API_KEY` in the
  backend `.env` and `VITE_API_KEY` in the frontend `.env` to the same value before
  deploying anywhere reachable outside your own machine — the shipped default
  (`dev-local-key-change-me`) is for local development only. This is a single-tenant
  "licensed instance" model (one key per deployment), not per-user accounts; see "Future
  improvements" for the multi-user upgrade path.
- Rate limiting (10 requests/60s/IP) on the compute-heavy `/api/analyze*` endpoints, to
  bound abuse and hosting cost.
- Upload content-type and size are validated server-side.
- CORS restricted to configured origins.
- No secrets in source; `.env` is gitignored, `.env.example` documents required vars.
- Uploaded files are stored with randomized filenames.
- Served evidence images under `/uploads` are not API-key gated (static file serving) —
  treat that path as low-sensitivity or put it behind your reverse proxy's own auth if
  evidence images are sensitive in your deployment.

## Privacy considerations

Evidence crops are images of vehicles (license plates may be visible depending on
footage). No facial data is intentionally captured, but any people visible in uploaded
footage are personal data — deployers are responsible for signage/consent per local
law before deploying this on public or semi-public roads.

## Limitations (read before demoing)

- **Speed is estimated, not legally certified.** It is derived from pixel displacement
  and a user-supplied pixels-per-meter calibration. Uncalibrated results can be
  meaningfully wrong. This system must not be represented as radar/lidar-grade
  enforcement equipment.
- **Detector**: MobileNet-SSD (2017, VOC-trained) is lightweight but dated. It performs
  best on roughly eye-level or moderately elevated views of vehicles at reasonable
  resolution. Steep overhead/CCTV angles and dashcam-style views of empty road (as
  found in some public traffic-camera sample datasets during development) produced
  near-zero detections — a production deployment should fine-tune or upgrade to a
  YOLO-family model trained on footage from the target camera's actual mounting angle.
- **Tracker**: the centroid tracker can occasionally split one real vehicle into two
  track IDs if detection confidence dips for a few frames — mitigated with a
  post-hoc track-stitching pass, but not eliminated. A Kalman-filter tracker (SORT/
  DeepSORT) would be the production upgrade.
- Demo clip is a synthetic composite (see "Demo instructions"), not real traffic footage.

## Business model

**Target customers**: schools, security companies, fleet/logistics operators,
municipalities, private estates, road safety NGOs.

**Revenue**: per-camera monthly SaaS subscription, fleet-wide monitoring bundle,
installation + hardware package, municipal multi-site contracts.

## Future improvements

- Swap MobileNet-SSD for a fine-tuned YOLOv8n on the deployment camera's real footage
- Kalman-filter tracking (SORT/DeepSORT) to eliminate ID fragmentation
- Automatic calibration via known lane-width reference points
- Live RTSP camera ingestion instead of upload-only
- Authentication + multi-tenant camera management
- License-plate blurring/redaction toggle for privacy-sensitive deployments

## Screenshots

Run the app locally (see "Running locally") and visit `/app` — the dashboard populates
after clicking **Run demo mode**.
