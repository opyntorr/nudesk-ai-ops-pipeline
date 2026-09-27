# Guía de Conexión: Google Workspace & n8n para nuDesk Operations Studio

Esta guía documenta los pasos para conectar el orquestador n8n con Google Workspace (Google Sheets, Gmail, Google Drive) tanto para la recepción de expedientes (Inputs) como para el registro y redacción de borradores (Outputs).

---

## 1. Métodos de Conexión en Google Cloud Console

### Opción A: Cuenta de Servicio (Service Account) — Recomendada para Google Sheets & Google Drive
Ideal para operaciones backend automatizadas (lectura y escritura desatendida de hojas de cálculo y carpetas en Drive sin caducidad de tokens).

1. Ingresar a [Google Cloud Console](https://console.cloud.google.com/).
2. Crear o seleccionar el proyecto corporativo (ej. `nudesk-operations-hub`).
3. En **APIs & Services > Library**, habilitar:
   - **Google Sheets API**
   - **Google Drive API**
4. Ir a **IAM & Admin > Service Accounts > Create Service Account**:
   - Nombre: `nudesk-n8n-bridge`
   - Rol: `Editor` o `Viewer/Editor de Drive`
5. Crear y descargar la llave en formato JSON (`Keys > Add Key > Create new key > JSON`).
6. Guardar el archivo en `config/service-account.json` (asegúrate de que no se suba a Git; ya está cubierto por `.gitignore`).
7. **Compartir las hojas de cálculo y carpetas:**
   - Crear las 3 hojas de cálculo principales:
     - `nuDesk_Credit_LOS_Pipeline`
     - `nuDesk_Commercial_Sales_CRM`
     - `nuDesk_Talent_Screening_Roster`
   - Dar permisos de **Editor** en cada hoja al correo de la Service Account (`nudesk-n8n-bridge@...iam.gserviceaccount.com`).

---

### Opción B: OAuth 2.0 Client ID — Requerida para Gmail (Creación de Borradores)
Permite a n8n interactuar con la bandeja de entrada del usuario autenticado (ej. BDR o reclutador) para crear borradores sin enviar correos sin supervisión humana.

1. En Google Cloud Console, ir a **APIs & Services > Credentials**.
2. Configurar la **OAuth Consent Screen** (Interna para tu organización de Google Workspace o Externa en modo prueba).
3. Habilitar la **Gmail API**.
4. Crear credencial **OAuth Client ID**:
   - Application Type: `Web application`
   - Name: `n8n nuDesk Ops Bridge`
   - Authorized Redirect URIs:
     - `http://localhost:5678/rest/oauth2-credential/callback`
5. Copiar el `Client ID` y `Client Secret` en la configuración de credenciales de n8n.

---

## 2. Importación de Flujos en n8n

El contenedor de n8n se encuentra activo en Docker (`http://localhost:5678`).

### Flujo de Salidas: Despacho de Triaje (`n8n_workflow_blueprint.json`)
1. Abrir n8n en el navegador: `http://localhost:5678`.
2. Crear un nuevo workflow o ir a **Workflows > Import from File**.
3. Seleccionar el archivo:
   `n8n_workflow_blueprint.json`
4. El workflow incluye:
   - **Webhook:** `POST /webhook/nudesk-triage`
   - **Normalizador de código:** Extrae y da formato a Credit, Sales y HR.
   - **Enrutador tripartito:**
     - **Credit:** Escribe en `Credit_LOS_Pipeline` y crea tareas en Asana.
     - **Sales:** Escribe en `Commercial_Sales_CRM` y crea borradores en Gmail.
     - **HR:** Escribe en `Talent_Screening_Roster` y crea borradores de seguimiento en Gmail.
5. Asociar las credenciales creadas de Google Sheets y Gmail a cada nodo respectivo.
6. Activar el Workflow (**Active = True**).

---

### Flujo de Entradas: Ingesta de Grabaciones y Archivos (`n8n_ingestion_blueprint.json`)
1. En n8n, ir a **Workflows > Import from File**.
2. Seleccionar el archivo:
   `n8n_ingestion_blueprint.json`
3. El workflow incluye:
   - **Webhook de Bots:** `POST /webhook/incoming-meeting` (para Read AI, Fireflies.ai o Zoom).
   - **Google Drive Trigger:** Escucha nuevos archivos en la carpeta de Drive `/nuDesk_Intake/`.
   - **Normalizador:** Extrae el transcript, asigna el módulo y genera el payload normalizado.
   - **Local Queue Bridge:** Ejecuta `scripts/ingest_incoming_file.py --stdin` para insertar el expediente directamente en la cola SQLite de nuDesk con `is_processed = 0` y timer SLA activo.
4. Activar el Workflow (**Active = True**).

---

## 3. Verificación de la Conexión de Extremo a Extremo

Ejecutar la suite de validación integrada:
```bash
.venv/bin/python scripts/test_n8n_pipeline.py
```

Esta prueba verifica automáticamente:
1. Ingesta de expediente de reunión en la cola FIFO con SLA activo.
2. Despacho HTTP 200 a n8n del memorando de Crédito.
3. Despacho HTTP 200 a n8n de Lead comercial y borrador de Gmail.
4. Despacho HTTP 200 a n8n de Evaluación de talento de RRHH.
5. Tolerancia a fallos en modo simulación cuando no hay red externa.
