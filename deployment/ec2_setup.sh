#!/usr/bin/env bash
# ==============================================================================
# AWS EC2 Setup & Automation Script for FastAPI URL Shortener
# ==============================================================================
set -e

echo "=========================================================="
echo "Iniciando configuración del Backend en Amazon EC2..."
echo "=========================================================="

CURRENT_USER=$(whoami)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_DIR}/backend"

echo "Usuario: ${CURRENT_USER}"
echo "Directorio Backend: ${BACKEND_DIR}"

# 1. Actualizar repositorios e instalar paquetes del sistema
echo -e "\n[1/6] Actualizando sistema e instalando dependencias (Python, Git)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl
elif command -v dnf &> /dev/null; then
    sudo dnf update -y
    sudo dnf install -y python3 python3-pip git curl
fi

# 2. Configurar entorno virtual de Python
echo -e "\n[2/6] Configurando entorno virtual de Python en ${BACKEND_DIR}/venv..."
cd "${BACKEND_DIR}"
if [ -d "venv" ]; then
    echo "Entorno virtual existente encontrado. Actualizando..."
else
    python3 -m venv venv
fi

# 3. Instalar librerías
echo -e "\n[3/6] Instalando FastAPI, Uvicorn, Boto3..."
"${BACKEND_DIR}/venv/bin/pip" install --upgrade pip
"${BACKEND_DIR}/venv/bin/pip" install -r requirements.txt

# 4. Detectar IP pública de la instancia EC2
echo -e "\n[4/6] Detectando IP pública de la instancia EC2..."
EC2_PUBLIC_IP=""

# Intentar vía IMDSv2
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null || true)
if [ -n "$TOKEN" ]; then
    EC2_PUBLIC_IP=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/public-ipv4" 2>/dev/null || true)
fi

# Fallback externo si no responde IMDS
if [ -z "$EC2_PUBLIC_IP" ]; then
    EC2_PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || curl -s https://ifconfig.me || echo "localhost")
fi

echo "IP pública detectada: ${EC2_PUBLIC_IP}"

# Crear o actualizar backend/.env
cat <<EOF > "${BACKEND_DIR}/.env"
AWS_REGION=us-east-1
DYNAMODB_TABLE=url_shortener
BASE_URL=http://${EC2_PUBLIC_IP}:8000
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=*
USE_MOCK_DB=false
EOF
echo "Archivo backend/.env generado exitosamente."

# 5. Configurar el servicio systemd
echo -e "\n[5/6] Instalando y activando servicio systemd..."
SERVICE_FILE="/etc/systemd/system/url-shortener.service"

sudo bash -c "cat <<EOF > ${SERVICE_FILE}
[Unit]
Description=AWS URL Shortener FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_USER}
WorkingDirectory=${BACKEND_DIR}
Environment=\"PATH=${BACKEND_DIR}/venv/bin\"
EnvironmentFile=${BACKEND_DIR}/.env
ExecStart=${BACKEND_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal
SyslogIdentifier=url-shortener

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable url-shortener
sudo systemctl restart url-shortener

# 6. Verificación
echo -e "\n[6/6] Verificando salud del servicio..."
sleep 3
if sudo systemctl is-active --quiet url-shortener; then
    echo "El servicio url-shortener está ACTIVO y en ejecución."
    HEALTH_RESP=$(curl -s http://localhost:8000/health || echo "Error")
    echo "Respuesta de salud: ${HEALTH_RESP}"
    echo ""
    echo "=========================================================="
    echo "DESPLIEGUE EN EC2 COMPLETADO CON ÉXITO!"
    echo "API pública disponible en: http://${EC2_PUBLIC_IP}:8000"
    echo "Documentación interactiva: http://${EC2_PUBLIC_IP}:8000/docs"
    echo "=========================================================="
else
    echo "ERROR: El servicio no pudo iniciar. Revisa los logs con: journalctl -u url-shortener -n 50 --no-pager"
    exit 1
fi
