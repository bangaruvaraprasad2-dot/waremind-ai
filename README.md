<<<<<<< HEAD
# waremind-ai
=======
# ⬡ WareMind AI
### Smart Warehouse Operations & Order Fulfillment Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg)](https://sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

WareMind AI is an enterprise-grade control tower and decision-support web application for modern warehouse operations and order fulfillment.

> **Core Philosophy**: *"Don't just show warehouse data. Detect operational problems, explain why they happened, recommend what should be done, and allow the warehouse manager to apply the recommended decision."*

---

## 🎯 Key Features

1. **Control Tower Dashboard**: Real-time KPI summary (Pending/Critical orders, Inventory units, Low stock alerts, Open exceptions, Fulfillment rate, 7-day throughput).
2. **Smart Priority Engine**: Multi-factor order scoring (Urgency 30%, Deadline 30%, Customer type 20%, Order age 10%, Business value 10%) mapping to `CRITICAL`, `HIGH`, `NORMAL`, `LOW`.
3. **Smart Allocation Engine**: Priority-aware stock reservation across zones, partial allocation handling, and shortage prevention.
4. **Exception Center**: Automated detection and one-click resolution for `LOW_STOCK`, `OUT_OF_STOCK`, `DAMAGED_ITEM`, `MISSING_ITEM`, `PICKING_DELAY`, `PACKING_DELAY`, `QUALITY_FAILURE`, and `ALLOCATION_CONFLICT`.
5. **Replenishment Engine**: Intelligent reorder level monitoring and supplier purchase recommendation.
6. **Picking & Route Optimization**: Zone-sequenced pick tasks minimizing warehouse travel distance.
7. **Bottleneck Detection**: Real-time stage analysis (Picking vs Packing vs Quality Check) recommending labor reallocation.
8. **AI Warehouse Copilot**: Rule-based & LLM-compatible assistant answering warehouse operational queries grounded strictly in live database records.
9. **🚨 Crisis Simulation Mode**: Special hackathon demo feature creating an instant inventory conflict with transparent system decision scoring and one-click resolution.

---

## 🏗️ Architecture & Technology Stack

```
WareMind-AI/
├── app.py                     # Main Flask Application Entry Point
├── config.py                  # Environment & App Configuration
├── requirements.txt           # Dependency Manifest
├── README.md                  # Project Documentation
├── database/                  # Database Layer
│   ├── __init__.py            # SQLAlchemy Instance Setup
│   ├── models.py              # 12 SQLAlchemy Schema Models
│   └── seed.py                # Comprehensive Mock Data Generator
├── routes/                    # RESTful Blueprint Controllers
│   ├── dashboard.py           # Dashboard KPIs, Alerts & Chart Endpoints
│   ├── inventory.py           # Inventory Search, Adjust & Damage Endpoints
│   ├── orders.py              # Order Fulfillment Lifecycle API
│   ├── exceptions.py          # Exception Center & Resolution API
│   ├── analytics.py           # Operational Performance Metrics API
│   ├── copilot.py             # AI Copilot Interface API
│   └── simulation.py          # Crisis Simulation API
├── services/                  # Business Logic & Decision Engines
│   ├── priority_engine.py     # Deterministic Priority Scoring
│   ├── allocation_engine.py   # Smart Stock Allocation & Shortage Logic
│   ├── replenishment_engine.py# Stock Threshold & Supplier Reorder Engine
│   ├── picking_engine.py      # Route Optimization & Zone Sequencing
│   ├── exception_engine.py    # Auto Exception Detection & Resolution
│   ├── bottleneck_engine.py   # Operational Stage Bottleneck Analyzer
│   └── copilot_service.py     # Grounded AI Assistance & Response Service
├── static/                    # Frontend Assets
│   ├── css/style.css          # Modern Dark Theme Glassmorphism Design System
│   └── js/dashboard.js        # Helper Utilities
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Core Layout & Topbar Clock
│   ├── dashboard.html         # Control Tower Dashboard & Chart.js Integration
│   ├── inventory.html         # Inventory Table & Adjustment Modals
│   ├── orders.html            # Orders List & Filters
│   ├── order_detail.html      # Order Timeline & Lifecycle Controls
│   ├── exceptions.html        # Exception Management Cards
│   ├── analytics.html         # Operations Analytics Charts
│   └── copilot.html           # AI Assistant Chat UI
└── tests/                     # Test Suites
    ├── test_priority.py       # Priority Scoring Unit Tests
    ├── test_allocation.py     # Allocation Engine Tests
    └── test_exceptions.py     # Exception Resolution Unit Tests
```

### Technology Stack
- **Backend**: Python 3.10+, Flask 3.0, Flask-SQLAlchemy 3.1, SQLite
- **Frontend**: Vanilla HTML5/CSS3 (Custom Dark Theme Design System), JavaScript (Fetch API), Chart.js 4.4
- **Testing**: Pytest

---

## ⚡ Quick Start Guide

### 1. Clone & Set Up Virtual Environment

```bash
# Clone the repository
git clone https://github.com/your-username/WareMind-AI.git
cd WareMind-AI

# Create virtual environment
python -m venv venv

# Activate environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux/macOS)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

The database will be automatically created and populated with realistic seed data on first boot:

```bash
python app.py
```

### 4. Access Web Interface

Open your browser and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Running Unit Tests

Run the full pytest suite:

```bash
python -m pytest tests/ -v
```

---

## 🎬 Hackathon Demonstration Scenario

1. **Control Tower**: Open the dashboard to view live warehouse KPIs, critical alerts, and operational charts.
2. **Order Lifecycle**: Navigate to **Orders** → Click **ORD-5001** (or any pending order) → View the **Decision Explanation** card showing how the Priority Score was calculated.
3. **Fulfillment Progress**:
   - Click **📦 Allocate Inventory**
   - Click **↻ Start Picking**
   - Click **✓ Complete Picking**
   - Click **✓ Complete Packing**
   - Click **🔍 Run QC**
   - Click **🚚 Dispatch Order**
4. **Exception Center**: Navigate to **Exception Center** → View open inventory or delay exceptions → Click **⚡ Apply Recommendation** to automatically execute the system decision and update inventory.
5. **AI Copilot**: Navigate to **AI Copilot** → Click **"Which orders are at risk?"** or ask **"Show me the bottleneck"** to receive grounded, real-time database answers.
6. **Crisis Simulation Mode**: Click the prominent **🚨 Simulate Crisis** button in the top navigation bar to trigger a live stock conflict scenario, analyze system reasoning, and execute the resolution decision.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
>>>>>>> 6f4f557 (Initial commit: WareMind AI Smart Warehouse Operations Platform)
