# Guía de Despliegue Paso a Paso en AWS

Esta guía detalla el procedimiento exacto para desplegar el acortador de enlaces en AWS, cubriendo la configuración de **Amazon DynamoDB**, **Amazon EC2** con **Roles IAM**, y **Amazon S3** con **Static Website Hosting**.

---

## Índice
1. [Paso 1: Crear la tabla en Amazon DynamoDB](#paso-1-crear-la-tabla-en-amazon-dynamodb)
2. [Paso 2: Crear la Política y el Rol IAM para EC2](#paso-2-crear-la-política-y-el-rol-iam-para-ec2)
3. [Paso 3: Lanzar y Configurar la Instancia Amazon EC2](#paso-3-lanzar-y-configurar-la-instancia-amazon-ec2)
4. [Paso 4: Desplegar el Backend FastAPI con systemd](#paso-4-desplegar-el-backend-fastapi-con-systemd)
5. [Paso 5: Desplegar el Frontend en Amazon S3](#paso-5-desplegar-el-frontend-en-amazon-s3)
6. [Paso 6: Pruebas de Funcionamiento de Extremo a Extremo](#paso-6-pruebas-de-funcionamiento-de-extremo-a-extremo)

---

## Paso 1: Crear la tabla en Amazon DynamoDB

### Desde la Consola de AWS:
1. Inicia sesión en la **Consola de AWS** y asegúrate de estar en la región deseada (ej. `us-east-1` N. Virginia).
2. Dirígete al servicio **DynamoDB** y haz clic en **Crear tabla** (Create table).
3. Configura los siguientes parámetros:
   - **Nombre de la tabla (Table name):** `url_shortener`
   - **Clave de partición (Partition key):** `short_code` (Tipo: `String`)
   - **Clave de ordenamiento (Sort key):** *(Dejar en blanco)*
4. En **Configuración de tabla (Table settings)**:
   - Selecciona **Personalizar configuración (Customize settings)**.
   - En **Modo de capacidad de lectura/escritura (Read/write capacity settings)** selecciona **Bajo demanda (On-demand)** para evitar cargos innecesarios en reposo.
5. Haz clic en **Crear tabla**. Espera unos segundos hasta que el estado cambie a **Activo (Active)**.

> **Nota:** No es necesario predefinir los atributos `original_url` ni `created_at` en el esquema, ya que DynamoDB es una base de datos NoSQL sin esquema rígido. El backend los insertará dinámicamente con cada registro.

---

## Paso 2: Crear la Política y el Rol IAM para EC2

Para cumplir con el requerimiento de seguridad (sin credenciales estáticas en código), crearemos un rol IAM con mínimos privilegios.

### 2.1 Crear la Política IAM:
1. Dirígete al servicio **IAM** -> **Políticas** (Policies) -> **Crear política** (Create policy).
2. Selecciona la pestaña **JSON** y pega el contenido del archivo `deployment/iam/dynamodb-policy.json`:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "DynamoDBShortenerLeastPrivilege",
         "Effect": "Allow",
         "Action": [
           "dynamodb:PutItem",
           "dynamodb:GetItem",
           "dynamodb:DescribeTable"
         ],
         "Resource": [
           "arn:aws:dynamodb:*:*:table/url_shortener"
         ]
       }
     ]
   }
   ```
3. Haz clic en **Siguiente**.
4. Asigna el nombre: `DynamoDBUrlShortenerPolicy`.
5. Haz clic en **Crear política**.

### 2.2 Crear el Rol IAM:
1. En el servicio **IAM**, ve a **Roles** -> **Crear rol** (Create role).
2. En **Tipo de entidad de confianza**, selecciona **Servicio de AWS (AWS service)**.
3. En **Caso de uso**, selecciona **EC2** y haz clic en **Siguiente**.
4. En el buscador de permisos, busca y marca la casilla de la política que acabas de crear: `DynamoDBUrlShortenerPolicy`.
5. Haz clic en **Siguiente**.
6. Nombre del rol: `EC2-DynamoDB-Shortener-Role`.
7. Haz clic en **Crear rol**.

---

## Paso 3: Lanzar y Configurar la Instancia Amazon EC2

1. Dirígete a **Amazon EC2** -> **Instancias** -> **Lanzar instancias** (Launch instances).
2. Configura los parámetros:
   - **Nombre:** `url-shortener-backend`
   - **AMI:** `Ubuntu Server 24.04 LTS` o `Ubuntu Server 22.04 LTS` (64 bits x86).
   - **Tipo de instancia:** `t2.micro` o `t3.micro` (Apta para la capa gratuita).
   - **Par de claves (Key pair):** Selecciona o crea un nuevo par de claves `.pem` para conectarte por SSH.
3. **Configuración de red (Security Group):**
   - Crear grupo de seguridad: `url-shortener-sg`.
   - Regla 1 (SSH): Tipo `SSH`, Puerto `22`, Origen `Mi IP` (o `0.0.0.0/0` para evaluación).
   - Regla 2 (API FastAPI): Tipo `Custom TCP`, Puerto `8000`, Origen `0.0.0.0/0` (Cualquier lugar).
4. **Detalles avanzados (Advanced details):**
   - En **Perfil de instancia de IAM (IAM instance profile)**, selecciona el rol creado: `EC2-DynamoDB-Shortener-Role`.
5. Haz clic en **Lanzar instancia** (Launch instance).
6. Una vez que la instancia esté en estado `Ejecutando` (Running), copia su **Dirección IPv4 pública** (ej. `54.210.120.30`).

---

## Paso 4: Desplegar el Backend FastAPI con systemd

### 4.1 Conectarse por SSH a la instancia:
Desde tu terminal o VSCode:
```bash
ssh -i "tu-llave.pem" ubuntu@<DIRECCIÓN_IP_PUBLICA_EC2>
```

### 4.2 Clonar el Repositorio:
```bash
git clone <URL_DE_TU_REPOSITORIO_GITHUB_O_GITLAB> examne2
cd examne2
```

### 4.3 Ejecutar el script automatizado:
Hemos preparado un script que realiza todo el aprovisionamiento, detección de IP pública y configuración de systemd en un solo paso:
```bash
chmod +x deployment/ec2_setup.sh
./deployment/ec2_setup.sh
```

El script automáticamente:
1. Actualiza el sistema e instala Python 3 y venv.
2. Crea el entorno virtual en `backend/venv` e instala FastAPI, Uvicorn y Boto3.
3. Detecta la IP pública de la instancia y configura `backend/.env`.
4. Instala y habilita el servicio systemd `/etc/systemd/system/url-shortener.service`.
5. Inicia el servicio y verifica el endpoint de salud `http://localhost:8000/health`.

### 4.4 Comandos útiles para gestionar el servicio:
```bash
# Ver el estado del servicio
sudo systemctl status url-shortener

# Reiniciar el servicio
sudo systemctl restart url-shortener

# Ver los logs en tiempo real
journalctl -u url-shortener -f
```

---

## Paso 5: Desplegar el Frontend en Amazon S3

### 5.1 Configurar el archivo de endpoint:
En tu máquina local, edita el archivo `frontend/config.js` y coloca la IP pública de tu EC2:
```javascript
window.API_BASE_URL = "http://<DIRECCIÓN_IP_PUBLICA_EC2>:8000";
```
*(Nota: la interfaz web también incluye un botón en la esquina superior derecha para cambiar o verificar la IP directamente desde el navegador en cualquier momento).*

### 5.2 Crear el Bucket en Amazon S3:
1. Dirígete a **Amazon S3** -> **Crear bucket**.
2. **Nombre del bucket:** Debe ser único a nivel global (ej. `acortador-enlaces-leo-cloud-2026`).
3. **Región:** Misma región de DynamoDB y EC2 (ej. `us-east-1`).
4. **Propiedad de objetos:** Lista de control de acceso (ACL) deshabilitada (recomendado).
5. **Bloqueo del acceso público:** **Desmarcar** la casilla "Bloquear todo el acceso público" y confirmar la advertencia (necesario para hospedar el sitio estático).
6. Haz clic en **Crear bucket**.

### 5.3 Habilitar el Alojamiento de Sitios Web Estáticos:
1. Entra al bucket recién creado y haz clic en la pestaña **Propiedades (Properties)**.
2. Baja hasta **Alojamiento de sitios web estáticos (Static website hosting)** y haz clic en **Editar**.
3. Selecciona **Habilitar (Enable)**.
4. Tipo de alojamiento: **Alojar un sitio web estático**.
5. **Documento de índice (Index document):** Escribe `index.html`.
6. Haz clic en **Guardar cambios**.
7. Copia la **URL del extremo del sitio web** generada (ej. `http://acortador-enlaces-leo-cloud-2026.s3-website-us-east-1.amazonaws.com`).

### 5.4 Configurar la Política de Acceso Público:
1. En el bucket, ve a la pestaña **Permisos (Permissions)** -> **Política de bucket (Bucket policy)** -> **Editar**.
2. Pega la política adaptada con el nombre de tu bucket (archivo `deployment/s3/bucket-policy.json`):
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObjectForStaticWebsite",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::<NOMBRE_DE_TU_BUCKET>/*"
       }
     ]
   }
   ```
3. Haz clic en **Guardar cambios**.

### 5.5 Subir los Archivos del Frontend:
1. En la pestaña **Objetos (Objects)** del bucket, haz clic en **Cargar (Upload)**.
2. Sube los siguientes 4 archivos de la carpeta `frontend/`:
   - `index.html`
   - `style.css`
   - `app.js`
   - `config.js`
3. Haz clic en **Cargar**.

---

## Paso 6: Pruebas de Funcionamiento de Extremo a Extremo

Abre tu navegador e ingresa a la URL del sitio estático de S3:

1. **Verificación de Conectividad:**
   - Observa el indicador en la cabecera: debe mostrar el punto verde `API EC2 Online (DynamoDB)`.

2. **Prueba de Creación de Enlace (Endpoint 1: POST /shorten):**
   - Pega una URL de destino (ej. `https://aws.amazon.com/es/dynamodb/`).
   - Presiona **Acortar Enlace**.
   - Comprueba que el backend genere un UUID v4 y muestre la URL corta generada (ej. `http://<IP_EC2>:8000/<UUID>`).

3. **Verificación en DynamoDB:**
   - Abre la consola de AWS -> **DynamoDB** -> **Tablas** -> `url_shortener` -> **Explorar elementos de la tabla**.
   - Comprueba que exista el registro con `short_code`, `original_url` y `created_at`.

4. **Prueba de Redirección Real (Endpoint 2: GET /{short_code}):**
   - Haz clic en el botón **Probar** o pega el enlace corto en una nueva pestaña del navegador.
   - Observa que el navegador navega automáticamente a la URL original mediante un código HTTP 307.

5. **Prueba de Consulta de Metadatos (Endpoint 3: GET /urls/{short_code}):**
   - En la interfaz web, cambia a la pestaña **Consultar por UUID**.
   - Pega el UUID y presiona **Consultar DynamoDB**.
   - Verifica que devuelva el objeto JSON completo con fecha de creación y URL original.

6. **Prueba de Error 404:**
   - Ingresa un UUID inexistente (ej. `00000000-0000-0000-0000-000000000000`).
   - Comprueba que devuelva `404 Not Found`.

7. **Prueba de Persistencia tras Reinicio:**
   - Conéctate a EC2 y reinicia el servicio:
     ```bash
     sudo systemctl restart url-shortener
     ```
   - Abre de nuevo el enlace corto en el navegador: la redirección sigue funcionando inmediatamente porque los datos están protegidos y persistidos en DynamoDB.
