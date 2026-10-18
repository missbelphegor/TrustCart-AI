from dataclasses import dataclass, asdict
import re
from .normalize import normalize, parse_price, fuzzy

@dataclass
class Slots:
    intent:str='product_search'; category:str|None=None; brand:str|None=None; color:str|None=None; material:str|None=None; size:str|None=None
    price_min:int|None=None; price_max:int|None=None; product_ref:str=''; policy_topic:str|None=None; stock_only:bool=False; sort:str|None=None
    compare_refs:list|None=None; unknown_entities:list|None=None; raw_normalized_query:str=''
    def to_dict(self): return asdict(self)

COMMON=set('show me find a the of for with in under below less than max upto up to price cost how much kitne ka is do you sell have want good best cheap cheapest nice something anything help choose order where my track status payment account returns return refund shipping delivery warranty policy stock available size it that already said and shirts please products me'.split())

def understand(query,vocab):
    q=normalize(query)
    corrected=[]
    for token in q.split():
        match=fuzzy(token,vocab.get('title_tokens',[]),.88) if len(token)>=4 else None
        corrected.append(match or token)
    q=' '.join(corrected); s=Slots(raw_normalized_query=q)
    # Parse from the original input so normalization does not turn a thousands
    # separator (for example 2,000) into a separate number.
    s.price_min,s.price_max=parse_price(query)
    for field in ('category','brand','color','material','size'):
        vals=vocab.get(field,[])
        for v in sorted(vals,key=len,reverse=True):
            if re.search(r'\b'+re.escape(v.lower())+r'\b',q): setattr(s,field,v); break
    if not s.category:
        # Infer a category from a product type only when that title word maps to one category.
        for word in q.split():
            if word.endswith('s') and word[:-1] in vocab.get('title_tokens',[]): word=word[:-1]
            cats=vocab.get('product_type_categories',{}).get(word,[])
            if len(cats)==1: s.category=next(iter(cats)); break
    if s.price_min is not None or s.price_max is not None or 'price' in q or 'cost' in q or 'kitne ka' in str(query).lower(): s.intent='price_lookup'
    if any(w in q.split() for w in ('compare','versus','vs')): s.intent='compare'
    if any(w in q for w in ('return','shipping','delivery','warranty','policy','refund')):
        s.intent='policy'; s.policy_topic=next((w for w in ('returns','shipping','warranty') if w in q or (w=='returns' and 'return' in q)),None)
    if any(w in q for w in ('order status','where is my order','track my','payment','my account')): s.intent='out_of_scope'
    if any(w in q for w in ('in stock','available','stock')): s.stock_only=True; s.intent='stock_check'
    if any(w in q for w in ('cheapest','sasta')): s.sort='cheapest'
    elif any(w in q for w in ('top rated','best rated','highest rated')): s.sort='best_rated'
    if 'compare' in q: s.intent='compare'
    s.product_ref=' '.join(w for w in q.split() if w in vocab.get('title_tokens',[]) and w not in ('blue','red','black','green','white','shoes','shoe','shirt','shirts','clothes','kurta','saree'))
    unknown=[]
    for token in q.split():
        if token in COMMON or token.isdigit() or len(token)<3: continue
        if token not in vocab.get('title_tokens',[]) and not any(token in str(v).lower() for k in ('category','brand','color','material','size') for v in vocab.get(k,[])):
            if token not in unknown: unknown.append(token)
    # Unknown terms alone do not reject when an in-catalogue type is present.
    if not any(t in vocab.get('title_tokens',[]) for t in q.split()) and not s.category and not s.product_ref and not unknown and s.intent=='product_search': s.intent='chitchat'
    s.unknown_entities=unknown
    return s
