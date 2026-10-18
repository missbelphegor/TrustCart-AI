from __future__ import annotations
import csv, json, re
from pathlib import Path
import config

def _records(path: Path):
    suffix=path.suffix.lower()
    if suffix=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
    if suffix in ('.jsonl','.ndjson'):
        return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
    if suffix=='.json':
        value=json.loads(path.read_text(encoding='utf-8')); return value if isinstance(value,list) else value.get('products',value.get('items',[]))
    if suffix=='.parquet':
        try:
            import pandas as pd
            return pd.read_parquet(path).fillna('').to_dict('records')
        except Exception as e: raise RuntimeError('Parquet input requires pandas and pyarrow') from e
    raise ValueError(f'Unsupported catalogue format: {suffix}')

def _num(v):
    try: return float(re.sub(r'[^\d.]','',str(v)))
    except: return None

def _stock(v):
    s=str(v or '').lower().strip()
    if s in ('1','true','yes','available','in stock','instock','true'): return True
    if s in ('0','false','no','out of stock','outofstock','unavailable'): return False
    return None

def load_catalog(path: Path|str=config.CATALOG_PATH):
    rows=_records(Path(path)); products=[]; seen=set(); issues=[]
    for i,row in enumerate(rows,1):
        r={str(k).strip().lower().replace(' ','_'):v for k,v in row.items()}
        attrs=r.get('attributes',{})
        if isinstance(attrs,str):
            try: attrs=json.loads(attrs)
            except: attrs={}
        if isinstance(attrs,dict):
            for k,v in attrs.items(): r.setdefault(str(k).lower().replace(' ','_'),v)
        pid=str(r.get('id') or r.get('product_id') or f'P{i:05d}').strip()
        if pid in seen: issues.append(f'duplicate id {pid} at row {i}'); pid=f'{pid}-{i}'
        seen.add(pid)
        title=str(r.get('title') or r.get('name') or '').strip()
        if not title: issues.append(f'missing title at row {i}'); continue
        p={'id':pid,'title':title,'description':str(r.get('description') or ''),'category':str(r.get('category') or 'Unknown'),'price':_num(r.get('price')),'stock':_stock(r.get('stock',r.get('stock_status'))),'rating':_num(r.get('rating',r.get('ratings')))}
        reserved={'id','product_id','title','name','description','category','price','stock','stock_status','rating','ratings','attributes'}
        for k,v in r.items():
            if k not in reserved and v not in (None,''): p[k]=str(v).strip()
        p['attributes']={k:v for k,v in p.items() if k not in ('id','title','description','category','price','stock','rating','attributes')}
        p['text']=' '.join([p['title'],p['category'],*p['attributes'].values(),p['description']])
        products.append(p)
    vocab={k:sorted({p.get(k,'').lower() for p in products if p.get(k)}) for k in ('category','brand','color','material','size')}
    vocab['title_tokens']=sorted({w for p in products for w in re.findall(r'[a-z0-9]+',p['title'].lower())})
    vocab['product_type_categories']={}
    for p in products:
        for word in re.findall(r'[a-z0-9]+',p['title'].lower()): vocab['product_type_categories'].setdefault(word,set()).add(p['category'])
    vocab['product_type_categories']={k:sorted(v) for k,v in vocab['product_type_categories'].items()}
    print(f'Loaded {len(products)} products; vocabulary sizes: '+', '.join(f'{k}={len(v)}' for k,v in vocab.items()))
    if issues: print(f'Data quality: {len(issues)} issue(s); first: {issues[0]}')
    return products,vocab,issues

def load_policy(path: Path|str=config.POLICY_PATH):
    raw=Path(path).read_text(encoding='utf-8'); chunks=[]; topic='general'; index=0; paragraphs=[]
    for line in raw.splitlines():
        line=line.strip()
        if not line: continue
        if len(line)<45 and not re.search(r'[.!?]',line):
            if paragraphs: chunks.append((topic,' '.join(paragraphs))); paragraphs=[]
            topic=re.sub(r'[^a-z]+','',line.lower()) or 'general'; index=0
        else: paragraphs.append(line)
    if paragraphs: chunks.append((topic,' '.join(paragraphs)))
    chunks=[{'id':f'POLICY:{t}.{i+1}','topic':t,'text':txt} for t,txt in chunks for i in (range(sum(1 for a,_ in chunks if a==t)),)] if False else chunks
    out=[]; counts={}
    for t,txt in chunks:
        counts[t]=counts.get(t,0)+1; out.append({'id':f'POLICY:{t}.{counts[t]}','topic':t,'text':txt})
    chunks=out
    return chunks
