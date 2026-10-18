import csv, time
from pathlib import Path
import config

class Timer:
    def __init__(self): self.start=time.perf_counter()
    def ms(self): return (time.perf_counter()-self.start)*1000

def log(row):
    config.REPORTS.mkdir(exist_ok=True); path=config.REPORTS/'query_log.csv'; exists=path.exists()
    with path.open('a',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(row));
        if not exists:w.writeheader()
        w.writerow(row)
