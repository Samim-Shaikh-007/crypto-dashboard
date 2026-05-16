# 📈 CryptoDash — Live Crypto Price Tracker

> A real-time cryptocurrency price tracker that scrapes BTC, ETH & BNB prices every 5 minutes, stores them in PostgreSQL, and visualises trends on a live Grafana dashboard — fully containerised with Docker and deployed to the cloud.

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?style=flat&logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-10.4.2-F46800?style=flat&logo=grafana&logoColor=white)
![Railway](https://img.shields.io/badge/Scraper-Railway-0B0D0E?style=flat&logo=railway&logoColor=white)
![Render](https://img.shields.io/badge/Dashboard-Render-46E3B7?style=flat&logo=render&logoColor=white)

---

## 🌐 Live Demo

| Service | URL |
|---|---|
| 📊 Grafana Dashboard | [crypto-grafana.onrender.com](https://crypto-grafana.onrender.com) |
| 🗄️ Database | Render PostgreSQL (cloud) |
| ⚙️ Scraper | Railway (always running) |

> **Login:** `admin` / `admin123`
> The dashboard auto-refreshes every 30 seconds with live prices.

---

## 🏗️ Architecture

```
CoinGecko API (free · no API key)
       │
       │  HTTP fetch every 300s
       ▼
 scraper.py  ──── INSERT ────▶  PostgreSQL (Render)
  [Railway]                          │
                                     │  SQL query every 30s
                                     ▼
                               Grafana Dashboard (Render)
                                     │
                                     │  HTTPS
                                     ▼
                             Browser (any device)
```

---

## 📊 Dashboard Panels

| Panel | Type | Description |
|---|---|---|
| Bitcoin (BTC) Price — USD | Time series | BTC price trend over selected time range |
| Ethereum (ETH) Price — USD | Time series | ETH price trend with purple line |
| BNB Price — USD | Time series | BNB price trend with yellow line |
| 24h Change % — All Coins | Bar gauge | Green = positive · Red = negative |
| Latest Prices | Table | Price, market cap, volume, 24h change, timestamp |

---

## 🗂️ Project Structure

```
crypto-dashboard/
├── scraper/
│   ├── scraper.py          # Fetches prices from CoinGecko → stores in PostgreSQL
│   ├── requirements.txt    # requests, psycopg2-binary
│   └── Dockerfile          # Multi-stage build, non-root user
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── postgres.yml        # Auto-connects Grafana to PostgreSQL
│       └── dashboards/
│           ├── provider.yml        # Dashboard file provider config
│           └── crypto.json         # Pre-built 5-panel dashboard
├── tests/
│   └── test_main.py        # Pytest test suite
├── docker-compose.yml      # Runs everything locally: Postgres + Scraper + Grafana
├── .gitlab-ci.yml          # CI/CD: test → build (ECR) → deploy (ECS)
├── railway.json            # Railway deployment config
└── README.md
```

---

## 🚀 Run Locally

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

```bash
# 1. Clone the repo
git clone https://github.com/Samim-Shaikh-007/crypto-dashboard.git
cd crypto-dashboard

# 2. Start everything with one command
docker compose up --build

# 3. Open Grafana
open http://localhost:3000
# Login: admin / admin
```

Wait ~60 seconds for the first data points to appear.

### Useful local commands

```bash
# Run in background
docker compose up -d --build

# Watch scraper logs
docker compose logs scraper -f

# Check all containers
docker compose ps

# Stop (keeps data)
docker compose stop

# Stop and remove containers (keeps data volume)
docker compose down

# Stop and delete everything including database
docker compose down -v
```

---

## ☁️ Cloud Deployment

This project is deployed across two free-tier platforms:

### Scraper → Railway

The Python scraper runs as a background worker on Railway.

1. Push repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Set Root Directory to `scraper`
4. Add environment variables:

```
DATABASE_URL   = postgresql://user:password@host/crypto
SCRAPE_INTERVAL = 300
```

### Dashboard → Render

Grafana is deployed as a Docker image on Render.

1. Go to [render.com](https://render.com) → New Web Service → Existing Image
2. Image: `grafana/grafana:10.4.2`
3. Add environment variables:

```
GF_SECURITY_ADMIN_USER     = admin
GF_SECURITY_ADMIN_PASSWORD = admin123
GF_AUTH_ANONYMOUS_ENABLED  = true
```

### Database → Render PostgreSQL

1. Render → New → PostgreSQL → Free plan
2. Copy the **External Database URL** → paste as `DATABASE_URL` in Railway

---

## ⚙️ CI/CD Pipeline (GitLab)

The `.gitlab-ci.yml` defines a 3-stage pipeline:

```
push to main
     │
     ├── test    → runs pytest automatically
     │
     ├── build   → builds Docker image → pushes to AWS ECR
     │              tagged with git commit SHA
     │
     └── deploy  → registers new ECS task definition
                    rolling update → manual trigger required
```

### Required GitLab CI/CD Variables

| Variable | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM user key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret |
| `AWS_DEFAULT_REGION` | e.g. `ap-south-1` |
| `ECR_REGISTRY` | e.g. `123456789.dkr.ecr.ap-south-1.amazonaws.com` |
| `ECR_REPOSITORY` | e.g. `crypto-scraper` |
| `ECS_CLUSTER` | Your ECS cluster name |
| `ECS_SERVICE` | Your ECS service name |
| `TASK_DEFINITION_FAMILY` | Your ECS task definition family |

---

## 🗄️ Database Schema

```sql
CREATE TABLE crypto_prices (
    id          SERIAL PRIMARY KEY,
    coin        VARCHAR(50)    NOT NULL,
    price_usd   NUMERIC(18,6)  NOT NULL,
    market_cap  NUMERIC(24,2),
    volume_24h  NUMERIC(24,2),
    change_24h  NUMERIC(8,4),
    fetched_at  TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE INDEX idx_crypto_coin_time
    ON crypto_prices (coin, fetched_at DESC);
```

---

## 🧪 Running Tests

```bash
pip install -r requirements.txt -r requirements-test.txt
pytest tests/ -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Scraper | Python 3.12, requests, psycopg2 |
| Database | PostgreSQL 16 |
| Dashboard | Grafana 10.4.2 |
| Containerisation | Docker, Docker Compose |
| Scraper Hosting | Railway |
| DB + Dashboard Hosting | Render |
| CI/CD | GitLab CI |
| Image Registry | AWS ECR |
| Container Orchestration | AWS ECS |

---

## ➕ Extending the Project

```bash
# Add more coins — edit scraper/scraper.py
COINS = ["bitcoin", "ethereum", "binancecoin", "solana", "cardano"]

# Change scrape interval — edit environment variable
SCRAPE_INTERVAL=120   # every 2 minutes

# Add Grafana alerts
# Grafana → Alerting → Alert rules → New alert rule
# Example: Alert when BTC drops below $70,000
```

---

## 📋 Roadmap

- [x] Python scraper with CoinGecko API
- [x] PostgreSQL time-series storage
- [x] Grafana dashboard with 5 panels
- [x] Docker Compose local setup
- [x] Railway deployment (scraper)
- [x] Render deployment (DB + Grafana)
- [x] GitLab CI/CD pipeline
- [ ] Grafana price drop alerts (email/Slack)
- [ ] Additional coins (SOL, ADA, DOGE)
- [ ] 7-day and 30-day trend panels
- [ ] Public read-only dashboard share link

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Samim Shaikh**
GitHub: [@Samim-Shaikh-007](https://github.com/Samim-Shaikh-007)

---

> Built as a DevOps portfolio project covering data engineering, Docker, CI/CD, and cloud deployment.
