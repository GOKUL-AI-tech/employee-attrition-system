#!/usr/bin/env bash
# macOS / Linux equivalent of start.bat
cd "$(dirname "$0")"

cd backend
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py &
BACKEND_PID=$!
trap "kill $BACKEND_PID" EXIT
cd ../frontend
[ -d node_modules ] || npm install
npm run dev
