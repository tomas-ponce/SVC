# SVC — Sistema de Vinculación para el Comercio (B2B SaaS)

[![Status](https://img.shields.io/badge/Status-Fase%202%20Construcción%20Completada%20(62%2F62%20CdU)-success)]()
[![Sprint](https://img.shields.io/badge/Sprint-Sprint%206%20Finalizado%20(v0.6.0)-0056b3)]()
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-009688)]()
[![Supabase](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Supabase-3ECF8E)]()

---

## 📌 1. Información Institucional y del Proyecto

* **Proyecto:** Sistema de Vinculación para el Comercio (SVC)
* **Autor:** Tomás Eloy Ponce
* **Carrera:** Ingeniería en Informática — Plan RR N° 280/11
* **Institución:** Universidad del Salvador (USAL) — Facultad de Ingeniería
* **Cátedra:** Seminario de Integración Profesional (Ciclo Lectivo 2026)
* **Docente Tutor:** Lic. Christian López Pasarón

---

## 🎯 2. Propósito y Alcance del Sistema

El **Sistema de Vinculación para el Comercio (SVC)** es una plataforma web B2B operada bajo el modelo **ASP (Application Service Provider / SaaS)**, diseñada para resolver la fragmentación y pérdida de información en las relaciones comerciales entre empresas, mayoristas, distribuidores y comercios minoristas.

### Límites de Alcance Estricto (Integración Delegada):
* **Fuera del Alcance:** SVC no procesa pagos de forma nativa ni gestiona flotas de transporte logístico.
* **Dentro del Alcance:** SVC actúa como un nexo de información y centralización:
  * **Procesamiento de Pagos (RF08 / RF11):** Integración con la API REST de MercadoPago mediante redirección parametrizada al Checkout y endpoints receptores de Webhooks para confirmaciones asíncronas de estado.
  * **Trazabilidad Logística (RF09 / RF13):** Consulta automatizada hacia APIs de proveedores logísticos (Correo Argentino, Andreani) consumiendo el Tracking ID vía HTTP GET y renderizando los estados en la plataforma.

---

## 📈 3. Estado de Avance y Planificación de Sprints (SDP IEEE 1058)

El proyecto se desarrolla bajo el estándar metodológico **Casos de Uso 2.0** en 6 Sprints iterativos dentro de la **Fase 2: Construcción Iterativa del MVP** (250 hs totales de desarrollo).

### 🏆 Estado Actual: ¡Fase 2 de Construcción 100% Completada! (62 / 62 CdU)

| Sprint | Paquete de Trabajo (WPT) | Casos de Uso (CdU) | Esfuerzo Planificado | Estado |
| :--- | :--- | :--- | :---: | :---: |
| **Sprint 1** | **WPT-01:** Gestión de Identidad y Administración Base | CdU01 a CdU09 | 40 hs | **Completado** |
| **Sprint 2** | **WPT-02:** Módulo de Inventario y Catálogo Privado | CdU43 a CdU47 | 30 hs | **Completado** |
| **Sprint 3** | **WPT-03:** Motor de Ofertas y Búsqueda Comercial | CdU10 a CdU12, CdU25 a CdU33 | 50 hs | **Completado** |
| **Sprint 4** | **WPT-05:** Red de Comunidades B2B | CdU13 a CdU24 | 30 hs | **Completado** |
| **Sprint 5** | **WPT-04:** Central de Negociación y Notificaciones | CdU34 a CdU42, CdU48 a CdU51, CdU62 | 50 hs | **Completado** |
| **Sprint 6** | **WPT-06:** Checkout y Logística<br>**WPT-07:** Reputación y Reseñas B2B | CdU52 a CdU57<br>CdU58 a CdU61 | 50 hs | **Completado** |
| **TOTAL** | **Fase 2: Construcción del MVP** | **62 Casos de Uso** | **250 hs** | **100% CERRADO** |

### 🚀 Próxima Etapa: Fase 3 — Transición y Cierre (80 hs planificadas)
1. **Etapa 3.1: Pruebas de Calidad (QA) y Auditoría Cruzada (40 hs):** Ejecución exhaustiva de pruebas E2E con Postman, validación de políticas RLS y auditoría de concurrencia.
2. **Etapa 3.2: Despliegue en Producción Cloud (20 hs):** Alojamiento del frontend en **Amazon Web Services (AWS)** y vinculación con backend y Supabase.
3. **Etapa 3.3: Documentación Histórica y Cierre (20 hs):** Balance definitivo, lecciones aprendidas y defensa ante la cátedra.

---

## 🛠️ 4. Pila Tecnológica & Arquitectura

* **Capa de Presentación (Frontend Web):**
  * HTML5 semántico, CSS3 moderno, JavaScript Vanilla (ES6+).
  * **Global Design System de SVC:** Bordes rectos de 90° (`border-radius: 0px`) en toda la UI, color interactivo corporativo `#0056b3`, tipografía *Inter*.
* **Capa de Aplicaciones (Backend):**
  * Python 3.11+ con **FastAPI** y servidor asíncrono **Uvicorn**.
  * Protocolo **WebSocket (WSS)** para chat de negociación y mensajería en tiempo real.
  * Autenticación segura mediante tokens **JWT** (JSON Web Tokens) y contraseñas hasheadas con **bcrypt**.
* **Capa de Datos & Seguridad (BaaS):**
  * Motor **PostgreSQL** alojado en **Supabase**.
  * Integridad transaccional **ACID** para reservas de inventario y órdenes de compra.
  * Políticas de seguridad por fila (**Row Level Security - RLS**) activas en todas las tablas del esquema público.

---

## 📂 5. Estructura del Repositorio

```text
SVC/
├── svc-backend/                      # Servidor API RESTful y WebSockets (FastAPI)
│   ├── app/
│   │   ├── core/                     # Configuración de seguridad, tokens JWT y hashing
│   │   ├── db/                       # Cliente y conexión con Supabase PostgreSQL
│   │   ├── routers/                  # Controladores REST por Caso de Uso
│   │   │   ├── auth.py               # Identidad y perfil (CdU01-09)
│   │   │   ├── inventario.py         # Inventario comercial (CdU43-47)
│   │   │   ├── publicaciones.py      # Ofertas y catálogo (CdU25-33)
│   │   │   ├── busqueda.py           # Filtros y búsqueda de comerciantes (CdU10-12)
│   │   │   ├── comunidades.py        # Redes sectoriales B2B (CdU13-24)
│   │   │   ├── chat.py               # Negociación en tiempo real por WebSockets (CdU34-42)
│   │   │   ├── notificaciones.py     # Centro de avisos y alertas (CdU48-51, 62)
│   │   │   ├── transacciones.py      # Checkout y trazabilidad logística (CdU53-55, 57)
│   │   │   ├── integraciones.py      # Credenciales MP y transportistas (CdU52, 56)
│   │   │   └── calificaciones.py     # Reputación y reseñas B2B (CdU58-61)
│   │   └── main.py                   # Punto de entrada de la aplicación FastAPI
│   └── requirements.txt              # Dependencias de Python
│
├── svc-frontend/                     # Cliente web estático (HTML5 / CSS3 / JS)
│   ├── login.html / registro.html    # Autenticación y acceso al sistema
│   ├── perfil.html / ver-perfil.html # Ficha comercial, integraciones y reputación
│   ├── inventario.html               # Gestión privada de stock
│   ├── muro-ventas.html              # Muro de oportunidades y ofertas
│   ├── detalle-publicacion.html      # Ficha de producto y reseñas
│   ├── generar-orden.html            # Formalización de compras
│   ├── historial-transacciones.html  # Compras, ventas, tracking y calificación
│   ├── chat.html                     # Negociación directa
│   ├── comunidades.html              # Directorio y gestión comunitaria
│   └── notificaciones.html           # Centro de alertas
│
├── README.md                         # Documentación en español
└── README_EN.md                      # Documentación en inglés
```

---

## 💻 6. Guía de Ejecución en Entorno Local

### Prerrequisitos
* Python 3.11+ instalado.
* Conexión a internet (para sincronización con Supabase y pasarelas de prueba).

### 1. Puesta en marcha del Backend
```bash
cd svc-backend
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Iniciar el servidor FastAPI en el puerto 8080:
uvicorn app.main:app --reload --port 8080
```
La documentación interactiva Swagger UI estará disponible en: `http://127.0.0.1:8080/docs`

### 2. Puesta en marcha del Frontend
Abrir los archivos `.html` de la carpeta `svc-frontend/` utilizando un servidor local estático (como la extensión *Live Server* de Visual Studio Code o `npx serve svc-frontend`) para acceder a `http://localhost:5500/login.html`.
