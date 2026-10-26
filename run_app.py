"""
Entry point to launch Marketing Budget Optimizer services (Streamlit Dashboard or FastAPI).
Usage:
    python run_app.py           # Launches interactive Streamlit Dashboard
    python run_app.py --api     # Launches FastAPI service on port 8000
"""

import sys
import subprocess
from pathlib import Path


def run():
    root = Path(__file__).resolve().parent
    if "--api" in sys.argv:
        print("🚀 Starting Marketing Budget Optimizer FastAPI on http://localhost:8000 ...")
        cmd = [sys.executable, "-m", "uvicorn", "marketing_budget_optimizer.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    else:
        print("📊 Starting Marketing Budget Optimizer Streamlit UI Dashboard ...")
        ui_path = root / "marketing_budget_optimizer" / "ui" / "dashboard.py"
        cmd = [sys.executable, "-m", "streamlit", "run", str(ui_path)]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nShutdown complete.")


if __name__ == "__main__":
    run()

