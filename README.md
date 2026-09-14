# AcousticPulse Backend

FastAPI + PostgreSQL backend for [AcousticPulse](https://github.com/shiny-retriever/AcousticPulse), a mechanical audio anomaly detection Android app.

Handles user authentication, and stores derived audio features (never raw audio) to sync a user's machines, calibration baselines, and scan history across devices and reinstalls.

## Features

- **JWT authentication** — signup/login with bcrypt-hashed passwords, bearer-token protected endpoints.
- **Multi-machine data model** — each user can register multiple machines, each with its own baseline calibration and scan history.
- **Privacy-conscious by design** — only derived spectral features (frequency-bin magnitudes, RMS energy, anomaly scores) are transmitted and stored. Raw audio never leaves the device.
- **Idempotent sync** — scan uploads are deduplicated via a client-generated scan ID, so retrying a sync after a dropped connection never creates duplicate records.

## Tech Stack

FastAPI · PostgreSQL · SQLAlchemy · Pydantic · python-jose (JWT) · passlib (bcrypt) · Uvicorn · Docker

## API Overview

| Endpoint | Method | Description |
|---|---|---|
| `/auth/signup` | POST | Create a new account |
| `/auth/login` | POST | Authenticate, receive a JWT |
| `/machines` | POST / GET | Create / list a user's machines |
| `/calibrate` | POST / GET | Store / retrieve a machine's baseline spectrum |
| `/diagnose` | POST / GET | Batch-sync / retrieve scan history |

Full interactive API documentation is auto-generated at `/docs` (Swagger UI) once running.

## Running locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

Requires a local PostgreSQL database and a `DATABASE_URL` environment variable (falls back to a local default if unset — see `database.py`).

## Deployment

Containerized with the included `Dockerfile`. Currently deployed on [Render](https://render.com) with a [Neon](https://neon.tech) PostgreSQL database.

## Companion App

The Android client for this backend: [AcousticPulse](https://github.com/shiny-retriever/AcousticPulse)

## Author

Meenu — [github.com/shiny-retriever](https://github.com/shiny-retriever)
