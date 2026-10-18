import hashlib, json, math, re, pickle
from pathlib import Path
import config

def tokens(text): return re.findall(r'[a-z0-9]+',str(text).lower())
def build_index(products,policy=(),cache_path=None):
    docs=[p['text'] for p in products]+[x['text'] for x in policy]; digest=hashlib.sha256('\n'.join(docs).encode()).hexdigest()
    path=Path(cache_path) if cache_path else config.CACHE/f'index_{digest}.pkl'
    if path.exists():
        try:
            cached=pickle.loads(path.read_bytes())
            if cached.get('hash')==digest:return cached
        except Exception: pass
    # Deterministic signed feature hashing supplies a dependency-free dense-like vector.
    vectors=[]
    for doc in docs:
        v={}
        for t in tokens(doc):
            h=int(hashlib.md5(t.encode()).hexdigest()[:8],16); i=h%128; sign=1 if h&128 else -1; v[i]=v.get(i,0)+sign
        norm=math.sqrt(sum(x*x for x in v.values())) or 1; vectors.append({i:x/norm for i,x in v.items()})
    result={'docs':docs,'tokens':[tokens(d) for d in docs],'vectors':vectors,'hash':digest,'policy_count':len(policy)}
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(pickle.dumps(result)); return result

def cosine(a,b): return sum(value*b.get(i,0.0) for i,value in a.items())
