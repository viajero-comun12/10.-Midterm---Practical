#!/usr/bin/env bash
# ==============================================================================
# Script de pruebas automatizadas con curl para la API en EC2
# Uso: ./test_api.sh [HOST_O_IP]
# Ejemplo: ./test_api.sh http://54.210.120.30:8000
# ==============================================================================

API_BASE="${1:-http://localhost:8000}"
API_BASE="${API_BASE%/}"

echo "=========================================================="
echo "Probando API URL Shortener en: ${API_BASE}"
echo "=========================================================="

# 1. Health check
echo -e "\n[1] Probando GET /health..."
curl -s -i "${API_BASE}/health" | head -n 15

# 2. Shorten URL (POST /shorten)
echo -e "\n\n[2] Probando POST /shorten..."
SHORT_RESP=$(curl -s -X POST "${API_BASE}/shorten" \
  -H "Content-Type: application/json" \
  -d '{"original_url": "https://www.example.com/articulos/arquitectura-cloud"}')

echo "Respuesta:"
echo "${SHORT_RESP}"

# Extraer short_code usando grep/sed o python si disponible
SHORT_CODE=$(echo "${SHORT_RESP}" | grep -o '"short_code":"[^"]*' | cut -d'"' -f4)

if [ -z "$SHORT_CODE" ]; then
    echo "ERROR: No se pudo obtener short_code de la respuesta."
    exit 1
fi

echo -e "\nUUID generado: ${SHORT_CODE}"

# 3. Inspect URL info (GET /urls/{short_code})
echo -e "\n[3] Probando GET /urls/${SHORT_CODE} (Endpoint 3)..."
curl -s -i "${API_BASE}/urls/${SHORT_CODE}" | head -n 20

# 4. Redirection test (GET /{short_code})
echo -e "\n\n[4] Probando Redirección GET /${SHORT_CODE} (Endpoint 2)..."
echo "Verificando código de estado 307 y cabecera Location:"
curl -s -i "${API_BASE}/${SHORT_CODE}" | grep -E "(HTTP/|location:|Location:)"

# 5. Non-existent UUID test (404)
echo -e "\n\n[5] Probando 404 con UUID inexistente..."
curl -s -i "${API_BASE}/00000000-0000-0000-0000-000000000000" | grep -E "HTTP/"

echo -e "\n=========================================================="
echo "Pruebas finalizadas."
echo "=========================================================="
