import json,sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.ingest import load_catalog,load_policy
import config

def main():
 products,_,_=load_catalog(); policy=load_policy(); rows=[]
 def add(q,typ,action,ids=(),facts=()): rows.append({'id':f'D{len(rows)+1:04d}','question':q,'type':typ,'expected_action':action,'expected_ids':list(ids),'expected_facts':list(facts),'notes':'synthetic demo fixture; labels derived or manually assigned'})
 for i in range(80):
  p=products[i%len(products)]
  if i%4==0: add(f"price of {p['title']}?",'answerable','ANSWER',[p['id']],['price'])
  elif i%4==1: add(f"is {p['title']} in stock",'answerable','ANSWER',[p['id']],['stock'])
  elif i%4==2: add(f"{p.get('color','')} {p.get('material','')} {p['title']} under 2k",'answerable','ANSWER',[p['id']],['price'])
  else: add('return policy','answerable','ANSWER',[policy[0]['id']],['policy'])
 ambiguous=['show me something nice','show me something','want something','show me anything nice','help me choose']*8
 for q in ambiguous: add(q,'ambiguous','CLARIFY')
 outside=['do you sell iPhones?','can I buy PlayStation here?','Nike shoes please','where is my order?','track my delivery','check my payment']*7
 for q in outside[:40]: add(q,'out-of-catalogue','REFUSE')
 traps=['price of the blue running shoe','blue running shoe stock?','kitne ka blue runner?','which blue running shoe costs less?']*10
 trapids=[p['id'] for p in products if p.get('color','').lower()=='blue' and 'running' in p['title'].lower()]
 for q in traps: add(q,'trap','CLARIFY',trapids)
 out=config.DATA/'dev_set.jsonl'; out.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n',encoding='utf-8')
 shuffled=list(rows); random.Random(17).shuffle(shuffled)
 for name,subset in [('dev_train.jsonl',shuffled[:100]),('dev_heldout.jsonl',shuffled[100:])]: (config.DATA/name).write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in subset)+'\n',encoding='utf-8')
 print(f'Wrote {len(rows)} demo questions and seeded 100/100 train/held-out splits')
if __name__=='__main__':main()
