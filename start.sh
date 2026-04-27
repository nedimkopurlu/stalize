#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Servisler kapatılıyor..."
  if [ -n "${BACKEND_PID}" ]; then kill "${BACKEND_PID}" 2>/dev/null || true; fi
  if [ -n "${FRONTEND_PID}" ]; then kill "${FRONTEND_PID}" 2>/dev/null || true; fi
}

trap cleanup SIGINT SIGTERM EXIT

port_is_listening() {
  lsof -tiTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1
}

echo "Stalize başlatılıyor..."

# Backend'i başlat
if port_is_listening 8000; then
  if curl -m 3 -fsS "http://127.0.0.1:8000/api/health" >/dev/null 2>&1; then
    echo "Backend zaten çalışıyor: http://localhost:8000"
  else
    echo "Port 8000 dolu ama backend sağlıklı cevap vermiyor."
    echo "Eski süreci kapatıp tekrar deneyin: lsof -tiTCP:8000 -sTCP:LISTEN | xargs kill"
    exit 1
  fi
else
  echo "Backend (FastAPI) başlatılıyor..."
  cd "${ROOT_DIR}/backend"

  if [ -x ".venv_repaired/bin/python3" ]; then
    PYTHON_BIN=".venv_repaired/bin/python3"
  elif [ -x ".venv/bin/python3" ]; then
    PYTHON_BIN=".venv/bin/python3"
  elif [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi

  "${PYTHON_BIN}" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
  BACKEND_PID=$!
fi

# Frontend'i başlat
if port_is_listening 3000; then
  echo "Frontend zaten çalışıyor: http://localhost:3000"
else
  echo "Frontend (Next.js) başlatılıyor..."
  cd "${ROOT_DIR}/frontend"
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

  if command -v nvm >/dev/null 2>&1; then
    nvm use 20 >/dev/null
  fi

  npm run dev &
  FRONTEND_PID=$!
fi

echo "Servisler ayakta."
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/docs"
echo "Kapatmak için CTRL+C'ye basın."

if [ -n "${BACKEND_PID}${FRONTEND_PID}" ]; then
  wait
else
  echo "Mevcut servisler kullanılıyor; bu pencereyi kapatabilirsiniz."
fi
