from pathlib import Path
import os

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
REPORTS = ROOT / 'reports'
CACHE = ROOT / '.cache'
CATALOG_PATH = Path(os.environ.get('TRUSTCART_CATALOG', DATA / 'catalogue.csv'))
POLICY_PATH = Path(os.environ.get('TRUSTCART_POLICY', DATA / 'policy.txt'))
MIN_CONFIDENCE = 0.015
AMBIGUITY_RATIO = 0.82
TOP_K = 20
RRF_K = 60
LLM_ENABLED = False
SEED = 17
