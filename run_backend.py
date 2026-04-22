import sys
import os

sys.path.insert(0, "/app")
os.environ.setdefault("PYTHONPATH", "/app")

from techpilot.techpilot import app  # noqa: E402 — triggers rx.App init + init_db
import uvicorn

uvicorn.run(app.api, host="127.0.0.1", port=8000, log_level="info")
