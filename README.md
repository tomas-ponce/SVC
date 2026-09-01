# SVC — Sistema de Vinculación para el Comercio (B2B SaaS)

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
  * **Procesamiento de Pagos (RF08 / RF11):** Integración con la API REST de MercadoPago mediante redirección parametrizada y endpoints receptores de Webhooks para confirmaciones asíncronas de estado.
  * **Trazabilidad Logística (RF09 / RF13):** Consulta automatizada hacia APIs de proveedores logísticos (Correo Argentino, Andreani) consumiendo el Tracking ID vía HTTP GET y renderizando los estados en la plataforma.

---

## 📈 3. Estado de Avance y Planificación de Sprints (SDP IEEE 1058)

El proyecto se desarrolla bajo el estándar metodológico **Casos de Uso 2.0** en 6 Sprints iterativos (250 hs totales de construcción):
```text
[Sprint 1: WPT-01] -> [Sprint 2: WPT-02] -> [Sprint 3: WPT-03] -> [Sprint 4: WPT-05] -> [Sprint 5: WPT-04] -> [Sprint 6: WPT-06/07]
      (40 hs)               (30 hs)               (50 hs)               (30 hs)               (50 hs)               (50 hs)
     COMPLETADO            COMPLETADO             ACTUAL
