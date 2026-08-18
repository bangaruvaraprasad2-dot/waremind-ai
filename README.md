# ⬡ WareMind AI
### Smart Warehouse Operations & Order Fulfillment Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-green.svg)](https://flask.palletsprojects.com/)
[![Render](https://img.shields.io/badge/Deploy-Render.com-informational.svg)](https://render.com/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

WareMind AI is an enterprise-grade control tower and decision-support web application for modern warehouse operations and order fulfillment.

> **Core Philosophy**: *"Don't just show warehouse data. Detect operational problems, explain why they happened, recommend what should be done, and allow the warehouse manager to apply the recommended decision."*

---

## 🚀 Deploy to Render.com (1-Click Setup)

To deploy **WareMind AI** live on Render:

1. Log in to **[Render.com](https://render.com)**.
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository: `https://github.com/bangaruvaraprasad2-dot/waremind-ai.git`.
4. Configure settings:
   - **Name**: `waremind-ai`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Create Web Service**! Render will deploy your live URL (e.g. `https://waremind-ai.onrender.com`).

---

## 🎯 Key Features

1. **Control Tower Dashboard**: Real-time KPI summary (Pending/Critical orders, Inventory units, Low stock alerts, Open exceptions, Fulfillment rate, 7-day throughput).
2. **Smart Priority Engine**: Multi-factor order scoring (Urgency 30%, Deadline 30%, Customer type 20%, Order age 10%, Business value 10%) mapping to `CRITICAL`, `HIGH`, `NORMAL`, `LOW`.
3. **Smart Allocation Engine**: Priority-aware stock reservation across zones, partial allocation handling, and shortage prevention.
4. **Exception Center**: Automated detection and one-click resolution for `LOW_STOCK`, `OUT_OF_STOCK`, `DAMAGED_ITEM`, `MISSING_ITEM`, `PICKING_DELAY`, `PACKING_DELAY`, `QUALITY_FAILURE`, and `ALLOCATION_CONFLICT`.
5. **Replenishment Engine**: Intelligent reorder level monitoring and supplier purchase recommendation.
6. **Picking & Route Optimization**: Zone-sequenced pick tasks minimizing warehouse travel distance.
7. **Bottleneck Detection**: Real-time stage analysis (Picking vs Packing vs Quality Check) recommending labor reallocation.
8. **AI Warehouse Copilot**: Grounded assistant with rich visual product & order cards answering warehouse operational queries.
9. **Dark / Light Theme Switcher**: Full theme mode toggle with persistent user preferences.
10. **🚨 Crisis Simulation Mode**: Special hackathon demo feature creating an instant inventory conflict with transparent system decision scoring and one-click resolution.

---

## 🏗️ Architecture & Technology Stack

```
WareMind-AI/
├── app.py                     # Main Flask Application Entry Point
├── config.py                  # Environment & App Configuration
├── render.yaml                # Render Infrastructure-as-Code Spec
├── Procfile                   # Web Process Declaration for Cloud Deployment
├── requirements.txt           # Dependency Manifest (with Gunicorn)
├── README.md                  # Project Documentation
├── database/                  # Database Layer
│   ├── __init__.py            # SQLAlchemy Instance Setup
│   ├── models.py              # 12 SQLAlchemy Schema Models
│   └── seed.py                # Comprehensive Mock Data Generator
├── routes/                    # RESTful Blueprint Controllers
├── services/                  # Business Logic & Decision Engines
├── static/                    # Frontend Assets & CSS System
├── templates/                 # Jinja2 HTML Templates
└── tests/                     # Test Suites
```

---

## ⚡ Quick Start Guide (Local)

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/bangaruvaraprasad2-dot/waremind-ai.git
cd waremind-ai
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies & Run

```bash
pip install -r requirements.txt
python app.py
```

Open your browser: 👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
