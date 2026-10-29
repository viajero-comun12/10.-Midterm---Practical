# 🚀 AWS URL Shortener (Acortador de Enlaces Cloud)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://www.python.org)
[![AWS EC2](https://img.shields.io/badge/AWS-EC2-FF9900.svg?style=flat&logo=amazonec2)](https://aws.amazon.com/ec2/)
[![AWS DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-4053D6.svg?style=flat&logo=amazondynamodb)](https://aws.amazon.com/dynamodb/)
[![AWS S3](https://img.shields.io/badge/AWS-S3-569A31.svg?style=flat&logo=amazons3)](https://aws.amazon.com/s3/)

Aplicación web cloud nativa para acortar URLs desarrollada y desplegada sobre servicios administrados de **Amazon Web Services (AWS)**. Permite registrar URLs largas, generar identificadores dinámicos mediante **UUID v4**, almacenar los registros en **Amazon DynamoDB**, y ejecutar redirecciones instantáneas mediante **HTTP 307 Temporary Redirect** a través de una API REST construida con **FastAPI** en **Amazon EC2**, consumida por una interfaz web moderna alojada en **Amazon S3**.

---

## 🏛️ Arquitectura de la Solución

```
                                      +-----------------------------+
                                      |   Amazon S3 (Frontend)      |
                                      |   Static Website Hosting    |
                                      |   HTML5 + CSS3 + JS         |
                                      +--------------+--------------+
                                                     |
                                        fetch()      |  CORS
                                        (HTTP/JSON)  v
+-----------------------+              +-----------------------------+
|   Usuario / Cliente   +------------->|   Amazon EC2 (Backend)      |
|   (Navegador Web)     |  GET /{uuid} |   FastAPI + Uvicorn         |
|                       |<-------------+   Servicio systemd          |
+-----------------------+  HTTP 307    +--------------+--------------+
                           Redirect                   |
                                             Boto3    |  IAM Role
                                        (Put/GetItem) v  (No Static Keys)
                                       +-----------------------------+
                                       |   Amazon DynamoDB           |
                                       |   Tabla: url_shortener      |
                                       |   Partition Key: short_code |
                                       +-----------------------------+
```

| Componente | Servicio AWS | Rol y Responsabilidad |
|---|---|---|
| **Frontend** | **Amazon S3** | Alojamiento de sitio web estático (HTML, CSS, JS). Proporciona la interfaz gráfica de usuario. |
| **Backend** | **Amazon EC2** | Instancia Linux ejecutando FastAPI con Uvicorn bajo `systemd`. Genera UUIDs y ejecuta la redirección HTTP 307. |
| **Base de Datos** | **Amazon DynamoDB** | Tabla NoSQL `url_shortener` con clave de partición `short_code` (UUID) para almacenamiento de baja latencia. |
| **Seguridad** | **AWS IAM** | Rol IAM asignado a la instancia EC2 con política de mínimo privilegio (`PutItem`, `GetItem`). **Sin claves estáticas**. |

---

## 📁 Estructura del Repositorio

```text
examne2/
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Módulo principal
│   │   ├── config.py         # Configuración y variables de entorno
│   │   ├── database.py       # Gestor Boto3 con IAM Role y fallback local
│   │   ├── models.py         # Esquemas Pydantic y validación de URLs
│   │   └── routes.py         # Controladores de los endpoints requeridos
│   ├── main.py               # Punto de entrada de la aplicación Uvicorn
│   ├── requirements.txt      # Dependencias: FastAPI, Uvicorn, Boto3, Pydantic
│   ├── .env.example          # Plantilla de variables de entorno
│   └── test_local.py         # Suite de pruebas automatizadas locales
├── frontend/
│   ├── index.html            # Interfaz moderna accesible y responsiva
│   ├── style.css             # Estilos modernos, dark mode y glassmorphism
│   ├── app.js                # Lógica del cliente, fetch a la API y portapapeles
│   └── config.js             # Configuración del endpoint de la API EC2
├── deployment/
│   ├── ec2_setup.sh          # Script automatizado de aprovisionamiento para EC2
│   ├── test_api.sh           # Script de pruebas con curl para la API
│   ├── iam/
│   │   ├── dynamodb-policy.json    # Política IAM de mínimos privilegios
│   │   └── trust-policy-ec2.json   # Política de confianza para EC2
│   ├── systemd/
│   │   └── url-shortener.service   # Definición del servicio systemd
│   └── s3/
│       ├── bucket-policy.json      # Política de lectura pública para S3
│       └── cors-configuration.json # Configuración CORS para S3
├── docs/
│   ├── ARQUITECTURA.md              # Documento técnico detallado con diagramas
│   ├── GUIA_DESPLIEGUE_PASO_A_PASO.md # Guía para desplegar en AWS
│   └── GUION_VIDEO_DEMO.md          # Guión paso a paso para el video de entrega
├── .gitignore
└── README.md
```

---

## 🔌 Especificación de la API REST

### 1. Crear un enlace corto
- **Método / Ruta:** `POST /shorten`
- **Descripción:** Recibe la URL original, genera un UUID v4 dinámico, almacena el registro en DynamoDB y devuelve la URL corta.
- **Cuerpo de la Solicitud (JSON):**
  ```json
  {
    "original_url": "https://www.example.com/articulos/arquitectura-cloud"
  }
  ```
- **Respuesta Exitosa (`201 Created`):**
  ```json
  {
    "short_code": "550e8400-e29b-41d4-a716-446655440000",
    "original_url": "https://www.example.com/articulos/arquitectura-cloud",
    "short_url": "http://<ip-publica-ec2>:8000/550e8400-e29b-41d4-a716-446655440000"
  }
  ```

### 2. Redireccionar al destino original
- **Método / Ruta:** `GET /{short_code}`
- **Descripción:** Busca el UUID en DynamoDB y responde con una redirección HTTP real (**307 Temporary Redirect**) hacia la URL original. El navegador navega automáticamente.
- **Códigos de Respuesta:**
  - `307 Temporary Redirect`: Cabecera `Location` con la URL original.
  - `404 Not Found`: Si el UUID no existe.

### 3. Consultar metadatos de un enlace
- **Método / Ruta:** `GET /urls/{short_code}`
- **Descripción:** Devuelve los datos almacenados en DynamoDB en formato JSON.
- **Respuesta Exitosa (`200 OK`):**
  ```json
  {
    "short_code": "550e8400-e29b-41d4-a716-446655440000",
    "original_url": "https://www.example.com/articulos/arquitectura-cloud",
    "created_at": "2026-10-29T21:40:00Z"
  }
  ```
- **Códigos de Respuesta:**
  - `404 Not Found`: Si el registro no existe.

### 4. Health Check
- **Método / Ruta:** `GET /health`
- **Descripción:** Verifica el estado operativo de la API y el modo de almacenamiento activo.

---

## 💻 Ejecución Local para Desarrollo y Pruebas

El proyecto cuenta con un modo de almacenamiento en memoria (`USE_MOCK_DB=true`) que permite probar todo el flujo en tu computadora sin necesidad de credenciales de AWS:

1. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv backend/venv
   # En Windows PowerShell:
   .\backend\venv\Scripts\Activate.ps1
   # En Linux/macOS:
   source backend/venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Ejecutar la suite de pruebas automatizadas:**
   ```bash
   python backend/test_local.py
   ```

4. **Iniciar el servidor backend:**
   ```bash
   python backend/main.py
   ```
   *La API estará disponible en `http://localhost:8000` y la documentación interactiva en `http://localhost:8000/docs`.*

5. **Iniciar la interfaz web:**
   Abre el archivo `frontend/index.html` en tu navegador o ejecuta:
   ```bash
   python -m http.server 3000 --directory frontend
   ```
   *Visita `http://localhost:3000`.*

---

## ☁️ Resumen del Despliegue en AWS

Para consultar la guía detallada paso a paso, revisa [docs/GUIA_DESPLIEGUE_PASO_A_PASO.md](docs/GUIA_DESPLIEGUE_PASO_A_PASO.md).

1. **DynamoDB:** Crear tabla `url_shortener` con clave de partición `short_code` (String).
2. **IAM:** Crear política `DynamoDBUrlShortenerPolicy` (desde `deployment/iam/dynamodb-policy.json`) y asociarla al rol `EC2-DynamoDB-Shortener-Role`.
3. **EC2:** Lanzar instancia Ubuntu con el rol IAM adjunto. Abrir los puertos `8000` (API) y `22` (SSH) en el Security Group.
4. **Backend:** Conectarse por SSH, clonar el repositorio y ejecutar:
   ```bash
   chmod +x deployment/ec2_setup.sh
   ./deployment/ec2_setup.sh
   ```
5. **S3:** Crear bucket, habilitar *Static Website Hosting*, aplicar la política pública (`deployment/s3/bucket-policy.json`), colocar la IP de EC2 en `frontend/config.js` y subir los archivos de `frontend/`.

---

## 🎥 Guión para el Video de Demostración

Para preparar la grabación exigida en el punto 11 de la entrega, consulta el guión completo con indicaciones exactas de tiempo y diálogo en [docs/GUION_VIDEO_DEMO.md](docs/GUION_VIDEO_DEMO.md).

---

## 🛡️ Principio de Seguridad Implementado

- **Sin credenciales fijas:** La aplicación no almacena `aws_access_key_id` ni `aws_secret_access_key` en archivos `.env` ni en el código.
- **Roles IAM:** La instancia EC2 utiliza credenciales temporales rotadas automáticamente por AWS.
- **Mínimo privilegio:** La política IAM solo otorga permisos `PutItem`, `GetItem` y `DescribeTable` sobre la tabla específica `url_shortener`.
