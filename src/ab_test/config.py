from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / 'data' / 'raw' / 'data.xlsx'
DEFAULT_OUTPUT = PROJECT_ROOT / 'reports'
STEPS = ['step1_opened', 'step2_entered', 'step3_confirmed', 'step4_success']
GROUPS = ['A', 'B']
ALPHA = 0.05
