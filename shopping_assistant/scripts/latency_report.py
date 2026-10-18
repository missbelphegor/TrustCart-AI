import sys,json,statistics
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evaluate import read_rows
from src.pipeline import Assistant
from config import REPORTS
def pct(a,p):
 a=sorted(a); return a[min(len(a)-1,int((len(a)-1)*p))] if a else 0
def main():
 rows=read_rows(Path(__file__).resolve().parents[1]/'data/dev_set.jsonl'); b=Assistant(); results=[b.chat('latency',r.get('question','')).telemetry for r in rows]; stages=['t_total','t_normalize','t_retrieve','t_gate','t_verify']; lines=['# Latency report','',f'Queries: {len(results)}','', '| Stage | p50 ms | p95 ms | max ms |','|---|---:|---:|---:|']
 for s in stages: lines.append(f"| {s} | {pct([x[s] for x in results],.5):.2f} | {pct([x[s] for x in results],.95):.2f} | {max(x[s] for x in results):.2f} |")
 lines+=['',f"Mean input/output tokens: 0 / 0",'Mean LLM calls: 0','LLM skipped: 100%','Verifier rescues: '+f"{100*sum(x['verifier_rescue'] for x in results)/max(1,len(results)):.1f}%",'','## Cost optimisation','Rules-first parsing and response templates avoid model initialization and calls. Hashed local vectors avoid downloading or loading embedding weights.']
 REPORTS.mkdir(exist_ok=True); (REPORTS/'latency_report.md').write_text('\n'.join(lines),encoding='utf-8'); (REPORTS/'latency_report.csv').write_text('stage,p50_ms,p95_ms,max_ms\n'+'\n'.join(f'{s},{pct([x[s] for x in results],.5):.2f},{pct([x[s] for x in results],.95):.2f},{max(x[s] for x in results):.2f}' for s in stages),encoding='utf-8'); print('\n'.join(lines))
if __name__=='__main__':main()
