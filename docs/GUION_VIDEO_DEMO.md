# Guión para el Video Explicativo de Entrega (Midterm AWS)

Este guión está estructurado para maximizar tu puntaje en la evaluación. Te guía segundo a segundo sobre qué mostrar en pantalla y qué explicar con precisión técnica.

**Duración recomendada:** 5 a 8 minutos.

---

## Estructura General del Video

| Bloque | Tiempo Sugerido | Tema Principal | Pantalla a Mostrar |
|---|---|---|---|
| **1. Introducción** | 0:00 - 0:45 | Presentación del estudiante y arquitectura de 3 capas | Diapositiva o Diagrama Mermaid en VSCode |
| **2. Amazon DynamoDB** | 0:45 - 1:45 | Explicación de la tabla y clave de partición | Consola AWS DynamoDB |
| **3. Amazon EC2 e IAM** | 1:45 - 3:00 | Instancia, Security Group, IAM Role y systemd | Consola AWS EC2 + Terminal SSH con systemctl |
| **4. Amazon S3** | 3:00 - 4:00 | Static Website Hosting, Bucket Policy y CORS | Consola AWS S3 |
| **5. Demostración en Vivo** | 4:00 - 6:30 | Acortar URL, ver registro en DynamoDB, redirección 307 real, consulta JSON y prueba de error 404 | Navegador web interactuando con la app |
| **6. Conclusión** | 6:30 - 7:00 | Resumen de buenas prácticas (sin credenciales hardcodeadas, desacoplamiento) | Cámara o VSCode |

---

## Guión Paso a Paso con Diálogos Sugeridos

### Bloque 1: Introducción (0:00 - 0:45)
- **Qué mostrar:** Tu rostro o la portada del proyecto con el diagrama de arquitectura (`docs/ARQUITECTURA.md`).
- **Qué decir:**
  > *"Hola, profesor y compañeros. Mi nombre es [Tu Nombre] y a continuación presento el desarrollo y despliegue del proyecto parcial: un acortador de enlaces cloud nativo desplegado en Amazon Web Services.*
  >
  > *La solución integra tres servicios principales de AWS: Amazon S3 para servir la interfaz estática, Amazon EC2 ejecutando una API REST construida con FastAPI y Uvicorn, y Amazon DynamoDB como base de datos NoSQL para persistir los enlaces con generación dinámica de identificadores UUID v4."*

---

### Bloque 2: Configuración de Amazon DynamoDB (0:45 - 1:45)
- **Qué mostrar:** La Consola de AWS en el servicio **DynamoDB** -> Tabla `url_shortener`.
- **Qué decir:**
  > *"Comenzamos revisando la capa de persistencia en Amazon DynamoDB.*
  >
  > *Hemos creado la tabla denominada `url_shortener`. Como se observa aquí, la clave de partición (Partition Key) es el atributo `short_code` de tipo String. Al ser DynamoDB una base de datos NoSQL de esquema flexible, cada ítem almacena además el atributo `original_url` con la dirección web de destino y `created_at` con la fecha y hora en formato ISO 8601.*
  >
  > *La tabla está configurada en modo de capacidad Bajo Demanda (On-Demand), garantizando escalabilidad automática y latencia de milisegundos para las consultas de redirección."*

---

### Bloque 3: Backend en Amazon EC2 y Rol IAM (1:45 - 3:00)
- **Qué mostrar:**
  1. Consola EC2 mostrando la instancia `url-shortener-backend`, su IP pública y el Security Group con puertos 22 y 8000.
  2. La sección de **Seguridad** de la instancia mostrando el **IAM Role** asociado (`EC2-DynamoDB-Shortener-Role`).
  3. Terminal SSH ejecutando `sudo systemctl status url-shortener`.
- **Qué decir:**
  > *"En la capa de aplicación, contamos con una instancia EC2 con Linux. En su Security Group hemos habilitado el puerto 8000 para el tráfico de la API pública y el puerto 22 para administración SSH.*
  >
  > *Un punto crítico de seguridad evaluado en el examen es que **no existen claves de acceso de AWS hardcodeadas en el código fuente**. En su lugar, asociamos a la instancia el rol IAM `EC2-DynamoDB-Shortener-Role`, el cual utiliza una política de mínimo privilegio que únicamente permite `PutItem`, `GetItem` y `DescribeTable` sobre nuestra tabla de DynamoDB. Boto3 obtiene automáticamente credenciales temporales a través del servicio de metadatos de la instancia.*
  >
  > *En la terminal podemos verificar que el backend en FastAPI se ejecuta bajo un servicio del sistema administrado por **systemd** (`url-shortener.service`). Esto asegura que si cerramos la sesión SSH o la instancia se reinicia, el servicio se reanuda de inmediato automáticamente."*

---

### Bloque 4: Frontend en Amazon S3 (3:00 - 4:00)
- **Qué mostrar:** Consola de Amazon S3 con el bucket, la pestaña **Propiedades** mostrando *Static website hosting: Habilitado* y los 4 archivos subidos (`index.html`, `style.css`, `app.js`, `config.js`).
- **Qué decir:**
  > *"Para la capa de presentación, utilizamos un bucket de Amazon S3 con la funcionalidad de Alojamiento de sitios web estáticos (Static Website Hosting).*
  >
  > *Hemos configurado una política de bucket pública de solo lectura para el método `s3:GetObject` y cargamos los archivos estáticos desarrollados en HTML5, CSS3 y JavaScript moderno sin frameworks pesados.*
  >
  > *La interfaz web consume la API de EC2 mediante llamadas asíncronas con `fetch()`. En el backend de FastAPI configuramos el middleware CORS para autorizar las peticiones provenientes del origen de nuestro bucket S3."*

---

### Bloque 5: Demostración en Vivo y Pruebas de Funcionamiento (4:00 - 6:30)
*(Esta es la sección más importante de la evaluación. Realízala con calma y claridad).*

- **Prueba 1: Carga y Conexión de la App**
  - **Qué mostrar:** Abre en el navegador la URL pública del endpoint S3 (ej. `http://tu-bucket.s3-website-us-east-1.amazonaws.com`).
  - **Qué decir:**
    > *"Accedemos a la URL pública del sitio estático en S3. En la esquina superior observamos el indicador de estado que confirma la conexión en tiempo real con la API en EC2."*

- **Prueba 2: Acortar un Enlace (POST /shorten - Endpoint 1)**
  - **Qué mostrar:** Ingresa en el formulario una URL real (ej. `https://aws.amazon.com/es/dynamodb/`) y haz clic en **Acortar Enlace**.
  - **Qué decir:**
    > *"Ingresamos una URL original y solicitamos su acortamiento. La interfaz envía la solicitud mediante `POST /shorten` a la IP de EC2. El backend genera dinámicamente un UUID v4, almacena el registro en DynamoDB y nos devuelve la URL corta generada: `http://<IP_EC2>:8000/<UUID>`.*
    >
    > *Probamos el botón de copiar, el cual ofrece confirmación interactiva en el portapapeles."*

- **Prueba 3: Comprobación de Persistencia en DynamoDB**
  - **Qué mostrar:** Cambia a la consola de AWS DynamoDB y presiona **Explorar elementos**.
  - **Qué decir:**
    > *"Si vamos a la consola de DynamoDB y refrescamos la tabla `url_shortener`, podemos ver que el elemento se ha persistido correctamente con su `short_code` (el UUID generado), la `original_url` y su marca de tiempo `created_at`."*

- **Prueba 4: Redirección Real (GET /{short_code} - Endpoint 2)**
  - **Qué mostrar:** Abre una nueva pestaña, pega el enlace corto y presiona Enter. Abre las Herramientas de Desarrollador (F12 -> Pestaña Red / Network) para mostrar el código `307 Temporary Redirect` y la cabecera `Location`.
  - **Qué decir:**
    > *"Ahora probamos la funcionalidad principal del acortador. Pegamos el enlace corto en el navegador. Como se observa en la pestaña Network de las herramientas de desarrollador, el backend de FastAPI no devuelve un JSON de texto, sino una respuesta HTTP de redirección real: **HTTP 307 Temporary Redirect**, navegando de manera instantánea y transparente a la página original de destino."*

- **Prueba 5: Consultar Metadatos (GET /urls/{short_code} - Endpoint 3)**
  - **Qué mostrar:** Vuelve a la interfaz web, ve a la pestaña **Consultar por UUID**, pega el UUID y presiona **Consultar DynamoDB**.
  - **Qué decir:**
    > *"El tercer endpoint requerido es `GET /urls/{short_code}`. Al consultar el UUID, el backend recupera la información directamente desde DynamoDB y nos retorna el objeto JSON con el UUID, la URL original y la fecha de creación."*

- **Prueba 6: Manejo de Error 404**
  - **Qué mostrar:** Pega un UUID inventado (ej. `11111111-1111-1111-1111-111111111111`) y haz la consulta o ingresa en la barra de direcciones.
  - **Qué decir:**
    > *"Si intentamos acceder a un UUID que no existe, el backend maneja adecuadamente la excepción y responde con un código de error **404 Not Found**, informando al usuario que el enlace no existe."*

---

### Bloque 6: Conclusión (6:30 - 7:00)
- **Qué mostrar:** El repositorio en GitHub o pantalla de despedida.
- **Qué decir:**
  > *"En conclusión, hemos implementado una solución robusta y completamente integrada: la interfaz estática servida desde Amazon S3, la lógica de negocio y redirección HTTP 307 ejecutándose en Amazon EC2 con administración systemd, la persistencia NoSQL escalable en Amazon DynamoDB y el principio de mínimo privilegio garantizado mediante un Rol IAM sin credenciales estáticas.*
  >
  > *El código fuente se encuentra disponible en el repositorio de GitHub adjunto. Muchas gracias por su atención."*
