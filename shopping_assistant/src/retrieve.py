from .index import tokens, cosine
import config

def rrf(sparse,dense,k=60):
    scores={}
    for ranking in (sparse,dense):
        for rank,item in enumerate(ranking,1): scores[item]=scores.get(item,0)+1/(k+rank)
    return sorted(scores,key=scores.get,reverse=True)

def retrieve(products,index,slots,top_k=20,ignore_price_max=False):
    filters=[('category',slots.category),('brand',slots.brand),('color',slots.color),('material',slots.material),('size',slots.size),('price_min',slots.price_min),('price_max',slots.price_max),('stock',True if slots.stock_only and not slots.product_ref else None)]
    active=[(k,v) for k,v in filters if v is not None and not (ignore_price_max and k=='price_max')]; relaxed=[]
    def ok(p,fs):
        for k,v in fs:
            if k=='price_min' and (p['price'] is None or p['price']<v): return False
            if k=='price_max' and (p['price'] is None or p['price']>v): return False
            if k=='stock' and p['stock'] is not v: return False
            if k not in ('price_min','price_max','stock') and str(p.get(k,'')).lower()!=str(v).lower(): return False
        return True
    subset=[i for i,p in enumerate(products) if ok(p,active)]
    if not subset: return [],relaxed
    q=' '.join(tokens(slots.raw_normalized_query)); qt=set(q.split())
    sparse=sorted(subset,key=lambda i:sum(index['tokens'][i].count(t) for t in qt),reverse=True)[:top_k]
    qv={};
    for t in qt:
        h=__import__('hashlib').md5(t.encode()).hexdigest(); n=int(h[:8],16); qv[n%128]=qv.get(n%128,0)+(1 if n&128 else -1)
    n=(sum(x*x for x in qv.values())**.5 or 1); qv={i:x/n for i,x in qv.items()}
    dense=sorted(subset,key=lambda i:cosine(qv,index['vectors'][i]),reverse=True)[:top_k]
    order=rrf(sparse,dense,config.RRF_K); rrf_scores={}
    for ranking in (sparse,dense):
        for rank,i in enumerate(ranking,1): rrf_scores[i]=rrf_scores.get(i,0)+1/(config.RRF_K+rank)
    max_score=max(rrf_scores.values(),default=1)
    found=[]
    for i in order[:top_k]:
        p=products[i]; bm=sum(index['tokens'][i].count(t) for t in qt); dc=cosine(qv,index['vectors'][i]); fused=rrf_scores[i]
        title=' '.join(tokens(p['title']))
        normalized=' '.join(tokens(slots.raw_normalized_query))
        exact=title in normalized
        if exact: fused+=1
        found.append({'product':p,'bm25':bm,'dense':dc,'fused':fused,'confidence':min(1,fused/max_score)})
    found.sort(key=lambda c:(c['confidence'],c['dense']),reverse=True)
    return found,relaxed
