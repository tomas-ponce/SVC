# SVC — Business Linking System (B2B SaaS)

[![Status](https://img.shields.io/badge/Status-Phase%202%20Construction%20Completed%20(62%2F62%20Use%20Cases)-success)]()
[![Sprint](https://img.shields.io/badge/Sprint-Sprint%206%20Completed%20(v0.6.0)-0056b3)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688)]()
[![Supabase](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Supabase-3ECF8E)]()

---

## 📌 1. Institutional and Project Information

* **Project:** Sistema de Vinculación para el Comercio (SVC)
* **Author:** Tomás Eloy Ponce
* **Degree:** Computer Engineering — Plan RR N° 280/11
* **Institution:** Universidad del Salvador (USAL) — Faculty of Engineering
* **Course:** Professional Integration Seminar (Academic Year 2026)
* **Faculty Advisor:** Prof. Christian López Pasarón

---

## 🎯 2. System Purpose and Scope

The **Sistema de Vinculación para el Comercio (SVC)** is a B2B web platform operated under the **ASP (Application Service Provider / SaaS)** model, designed to solve information fragmentation and lost business opportunities among enterprises, wholesalers, distributors, and retail businesses.

### Strict Scope Boundaries (Delegated Integration):
* **Out of Scope:** SVC does not natively process monetary payments or manage physical transport logistics fleets.
* **In Scope:** SVC acts as an information hub and centralization bridge:
  * **Payment Processing (RF08 / RF11):** Integration with Mercado Pago REST API via parameterized checkout redirection and Webhook endpoints for asynchronous payment status confirmations.
  * **Logistics Traceability (RF09 / RF13):** Automated queries to third-party shipping APIs (Correo Argentino, Andreani) sending the Tracking ID via HTTP GET and displaying real-time tracking updates inside the platform.

---

## 📈 3. Progress and Sprint Planning (SDP IEEE 1058)

The project is developed under the **Use Cases 2.0** methodology across 6 iterative Sprints within **Phase 2: Iterative Construction of the MVP** (250 total planned development hours).

### 🏆 Current Status: Phase 2 Construction 100% Completed! (62 / 62 Use Cases)

| Sprint | Work Package (WPT) | Use Cases (CdU) | Planned Effort | Status |
| :--- | :--- | :--- | :---: | :---: |
| **Sprint 1** | **WPT-01:** Identity Management & Core Administration | CdU01 to CdU09 | 40 hrs | **Completed** |
| **Sprint 2** | **WPT-02:** Inventory Module & Private Catalog | CdU43 to CdU47 | 30 hrs | **Completed** |
| **Sprint 3** | **WPT-03:** Commercial Offers & Search Engine | CdU10 to CdU12, CdU25 to CdU33 | 50 hrs | **Completed** |
| **Sprint 4** | **WPT-05:** B2B Communities Network | CdU13 to CdU24 | 30 hrs | **Completed** |
| **Sprint 5** | **WPT-04:** Negotiation Central & Notifications Hub | CdU34 to CdU42, CdU48 to CdU51, CdU62 | 50 hrs | **Completed** |
| **Sprint 6** | **WPT-06:** Checkout & Logistics<br>**WPT-07:** B2B Reputation & Reviews | CdU52 to CdU57<br>CdU58 to CdU61 | 50 hrs | **Completed** |
| **TOTAL** | **Phase 2: MVP Construction** | **62 Use Cases** | **250 hrs** | **100% CLOSED** |

### 🚀 Next Stage: Phase 3 — Transition and Closing (80 planned hours)
1. **Stage 3.1: Quality Assurance (QA) & Cross-Auditing (40 hrs):** Exhaustive E2E testing with Postman, RLS policy validation, and concurrency audits.
2. **Stage 3.2: Cloud Production Deployment (20 hrs):** Web frontend hosting on **Amazon Web Services (AWS)** and integration with backend and Supabase.
3. **Stage 3.3: Historical Documentation & Defense (20 hrs):** Final project balance, lessons learned, and oral academic defense.

---

## 🛠️ 4. Technology Stack & Architecture

* **Presentation Layer (Web Frontend):**
  * Semantic HTML5, modern CSS3, Vanilla JavaScript (ES6+).
  * **SVC Global Design System:** Strict 90-degree corners (`border-radius: 0px`) throughout the UI, corporate action color `#0056b3`, *Inter* typography.
* **Application Layer (Backend):**
  * Python 3.11+ powered by **FastAPI** and the **Uvicorn** asynchronous ASGI server.
  * Bidirectional **WebSocket (WSS)** protocol for real-time negotiation chat and messaging.
  * Secure authentication via **JWT** (JSON Web Tokens) with passwords hashed using **bcrypt**.
* **Data Layer & Security (BaaS):**
  * **PostgreSQL** relational engine hosted on **Supabase**.
  * Strict **ACID** transaction guarantees for inventory reservation and commercial orders.
  * Active **Row Level Security (RLS)** policies protecting all public schema tables.

---

## 📂 5. Repository Structure

```text
SVC/
├── svc-backend/                      # RESTful API and WebSockets server (FastAPI)
│   ├── app/
│   │   ├── core/                     # Security configuration, JWT tokens, and password hashing
│   │   ├── db/                       # Supabase PostgreSQL client and connection
│   │   ├── routers/                  # REST controllers by Use Case
│   │   │   ├── auth.py               # Identity and user profile (CdU01-09)
│   │   │   ├── inventario.py         # Commercial inventory (CdU43-47)
│   │   │   ├── publicaciones.py      # Sales offers and catalog (CdU25-33)
│   │   │   ├── busqueda.py           # Filters and merchant search (CdU10-12)
│   │   │   ├── comunidades.py        # B2B sectorial communities (CdU13-24)
│   │   │   ├── chat.py               # Real-time WebSocket negotiation (CdU34-42)
│   │   │   ├── notificaciones.py     # Notification center and alerts (CdU48-51, 62)
│   │   │   ├── transacciones.py      # Checkout and logistics tracking (CdU53-55, 57)
│   │   │   ├── integraciones.py      # MP credentials and carriers (CdU52, 56)
│   │   │   └── calificaciones.py     # B2B reputation and reviews (CdU58-61)
│   │   └── main.py                   # FastAPI application entry point
│   └── requirements.txt              # Python runtime dependencies
│
├── svc-frontend/                     # Static web client (HTML5 / CSS3 / JS)
│   ├── login.html / registro.html    # Authentication and system access
│   ├── perfil.html / ver-perfil.html # Business profile, integrations, and reputation
│   ├── inventario.html               # Private stock management
│   ├── muro-ventas.html              # Commercial opportunities wall
│   ├── detalle-publicacion.html      # Product datasheet and reviews
│   ├── generar-orden.html            # Commercial purchase formalization
│   ├── historial-transacciones.html  # Purchases, sales, tracking, and rating
│   ├── chat.html                     # Direct negotiation chat
│   ├── comunidades.html              # Directory and community management
│   └── notificaciones.html           # Alert center
│
├── README.md                         # Spanish documentation
└── README_EN.md                      # English documentation
```

---

## 💻 6. Local Environment Setup Guide

### Prerequisites
* Python 3.11+ installed.
* Active internet connection (for Supabase and sandbox payment gateways).

### 1. Backend Setup
```bash
cd svc-backend
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Start FastAPI server on port 8080:
uvicorn app.main:app --reload --port 8080
```
Interactive Swagger UI documentation will be available at: `http://127.0.0.1:8080/docs`

### 2. Frontend Setup
Open the `.html` files in the `svc-frontend/` directory using a local static server (e.g., Visual Studio Code *Live Server* extension or `npx serve svc-frontend`) and navigate to `http://localhost:5500/login.html`.
