"""Запуск из исходников: python run_analysis.py [--input ...] [--output ...]."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from ab_test.pipeline import main

if __name__ == '__main__':
    main()
