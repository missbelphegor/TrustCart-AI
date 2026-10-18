import argparse,json,csv,sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from src.pipeline import Assistant
from src.verifier import verify
from config import REPORTS

def read_rows(p):
 s=Path(p).read_text(encoding='utf-8')
 if Path(p).suffix=='.jsonl': return [json.loads(x) for x in s.splitlines() if x.strip()]
 d=json.loads(s); return d if isinstance(d,list) else d.get('questions',[])
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--questions',required=True); ap.add_argument('--labels'); ap.add_argument('--out',default=str(REPORTS)); a=ap.parse_args(); rows=read_rows(a.questions); bot=Assistant(); out=[]; conf=collections.Counter(); cats=collections.defaultdict(lambda:[0,0]); hallucinated=0; grounded=[]; hits=[]
 for i,row in enumerate(rows):
  q=row.get('question',row.get('query','')); expected=row.get('expected_action',row.get('expected_behavior','ANSWER')).upper(); expected={'ANSWERABLE':'ANSWER','AMBIGUOUS':'CLARIFY','OUT-OF-CATALOGUE':'REFUSE','OUT_OF_CATALOGUE':'REFUSE','TRAP':'CLARIFY'}.get(expected,expected)
  r=bot.chat(f'eval-{i}',q); conf[(expected,r.action)]+=1; cat=row.get('type','unknown'); cats[cat][1]+=1; cats[cat][0]+=expected==r.action
  ids=row.get('expected_ids',[]); hit=not ids or any(f'[{pid}]' in r.text for pid in ids); hits.append(hit)
  v=verify(r.text,{'products':bot.products,'policy':bot.policy}); grounded.extend(c['supported'] for c in v.claims); hallucinated+=any((not c['supported'] and '₹' in c['sentence']) for c in v.claims)
  out.append({'id':row.get('id',i),'question':q,'type':cat,'expected_action':expected,'predicted_action':r.action,'response':r.text,'expected_ids':','.join(ids),'id_hit':hit,'grounded':v.valid,'reason':r.debug['reason']})
 dest=Path(a.out); dest.mkdir(parents=True,exist_ok=True)
 with (dest/'eval_details.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=out[0].keys());w.writeheader();w.writerows(out)
 total=max(1,len(rows)); refusal=sum(x==y for (x,y),n in conf.items() for _ in range(n))/total; ground=sum(grounded)/len(grounded) if grounded else 1; helpf=sum(hits)/total; score=max(0,.35*ground+.30*refusal+.35*helpf-5*hallucinated/total)
 summary={'n':len(rows),'behaviour_accuracy':refusal,'grounded_claim_precision':ground,'zero_unsupported_responses':sum(x['grounded'] for x in out)/total,'hallucinated_price_count':hallucinated,'helpfulness_id_recall':helpf,'combined_score':score,'by_type':{k:v[0]/max(1,v[1]) for k,v in cats.items()},'confusion_matrix':{f'{x}->{y}':n for (x,y),n in conf.items()}}
 (dest/'eval_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 (dest/'confusion_matrix.txt').write_text(json.dumps(summary['confusion_matrix'],indent=2),encoding='utf-8')
 print(json.dumps(summary,indent=2)); print('Top failures:'); print('\n'.join(f"{x['id']} {x['question']} [{x['expected_action']}->{x['predicted_action']}] {x['reason']}" for x in out if x['expected_action']!=x['predicted_action'])[:4000])
if __name__=='__main__':main()
