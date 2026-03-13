# 📄 Document Generation Service — Cloud Run

Microservicio que genera contratos Word (.docx) a partir de un template,
reemplazando placeholders con datos recibidos desde Zapier (o cualquier webhook).

## Archivos incluidos

```
docx-service/
├── main.py           # Aplicación Flask
├── requirements.txt  # Dependencias Python
├── Dockerfile        # Imagen Docker para Cloud Run
├── template.docx     # Tu template con logos y firmas
└── README.md         # Este archivo
```

---

## 🚀 Despliegue en Google Cloud Run

### Prerequisitos
- Cuenta en Google Cloud con un proyecto activo
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) instalado

### Paso 1 — Autenticarse y configurar proyecto

```bash
gcloud auth login
gcloud config set project TU_PROJECT_ID
```

### Paso 2 — Habilitar APIs necesarias

```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Paso 3 — Desplegar (un solo comando)

```bash
cd docx-service

gcloud run deploy docx-generator \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

Al finalizar, Cloud Run te dará una URL como:
`https://docx-generator-xxxx-uc.a.run.app`

---

## 🔌 Endpoints

| Método | Ruta        | Descripción                          |
|--------|-------------|--------------------------------------|
| GET    | `/health`   | Verifica que el servicio está activo |
| GET    | `/fields`   | Lista todos los campos del template  |
| POST   | `/generate` | Genera y devuelve el documento .docx |

---

## 📨 Ejemplo de llamado (cURL)

```bash
curl -X POST https://TU-URL.run.app/generate \
  -H "Content-Type: application/json" \
  -d '{
    "date_format_july22-2025": "July 22, 2025",
    "client_name": "John Smith",
    "Address_1": "123 Main Street",
    "Address_2": "Suite 100",
    "Zip_code": "78701",
    "subdivision": "Oak Creek Estates",
    "Project_Address": "456 Oak Lane",
    "Block": "12",
    "Lot": "34",
    "City": "Austin",
    "print_date": "July 22, 2025",
    "IRC": "2021",
    "Soils_report_source": "Geotech Labs Inc.",
    "Soils_report_number": "GT-2024-0099",
    "Soils_report_date_formatted_july9-2024": "July 9, 2024",
    "filename": "contrato_john_smith.docx"
  }' \
  --output contrato_generado.docx
```

---

## ⚡ Configuración en Zapier

### Zap: Formulario / CRM → Generar contrato → Guardar en Drive

1. **Trigger**: Google Sheets / Typeform / HubSpot / lo que uses
2. **Action**: `Webhooks by Zapier` → `POST`
   - **URL**: `https://TU-URL.run.app/generate`
   - **Payload Type**: `JSON`
   - **Data**: mapea cada campo del trigger al JSON del endpoint
   - **Response**: marca "Unflatten" = No

3. **Action**: `Google Drive` → `Upload File`
   - **File**: usa el output del paso anterior (response body)
   - **File Name**: `contrato_{{client_name}}_{{date}}.docx`
   - **Folder**: tu carpeta de contratos

### ⚠️ Nota sobre el archivo en Zapier
Zapier recibe el archivo como `Binary Content`. En el paso de Google Drive,
selecciona el campo `Response Body` del webhook como el archivo a subir.

---

## 🔒 Seguridad (opcional pero recomendado)

Para proteger el endpoint con un API key simple:

1. En Cloud Run, agrega una variable de entorno `API_KEY=tu-clave-secreta`
2. En `main.py`, agrega antes del generate:

```python
API_KEY = os.environ.get("API_KEY")
if API_KEY and request.headers.get("X-API-Key") != API_KEY:
    return jsonify({"error": "Unauthorized"}), 401
```

3. En Zapier, agrega el header `X-API-Key: tu-clave-secreta`

---

## 📊 Costos estimados

| Métrica           | Capa gratuita       |
|-------------------|---------------------|
| Invocaciones      | 2,000,000 / mes     |
| Tiempo de CPU     | 360,000 vCPU-seg    |
| Memoria           | 180,000 GB-seg      |

Para un uso típico de contratos (1,000–10,000/mes), **el costo es $0**.

---

## Campos del template

| Placeholder                                   | Descripción                    |
|-----------------------------------------------|--------------------------------|
| `date_format_july22-2025`                     | Fecha del documento            |
| `client_name`                                 | Nombre del cliente             |
| `Address_1`                                   | Dirección línea 1              |
| `Address_2`                                   | Dirección línea 2              |
| `Zip_code`                                    | Código postal                  |
| `subdivision`                                 | Nombre del proyecto/subdivisión|
| `Project_Address`                             | Dirección del proyecto         |
| `Block`                                       | Bloque                         |
| `Lot`                                         | Lote                           |
| `City`                                        | Ciudad                         |
| `print_date`                                  | Fecha del plano de fundación   |
| `IRC`                                         | Código IRC (ej: 2021)          |
| `Soils_report_source`                         | Fuente del reporte de suelos   |
| `Soils_report_number`                         | Número del reporte             |
| `Soils_report_date_formatted_july9-2024`      | Fecha del reporte de suelos    |
