killall -9 uvicorn vite playwright >/dev/null 2>&1 || true
.venv/bin/python -m uvicorn backend.app.main:app --port 8000 >/dev/null 2>&1 &
BACKEND_PID=$!
sleep 2
cd frontend
npm run dev -- --port 4173 >/dev/null 2>&1 &
FRONTEND_PID=$!
sleep 4
cd ..
npx playwright test e2e/screenshots.spec.ts --project=chromium > playwright_out.txt 2>&1
kill $BACKEND_PID $FRONTEND_PID >/dev/null 2>&1 || true
