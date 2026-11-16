"""CLI: train the model from the SQLite database.   python ml/train.py"""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))
from app import create_app  # noqa: E402
from ml_service import retrain  # noqa: E402

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Model trained:", retrain())
