class Session:
    def __init__(self): self.filters={}; self.last_candidates=[]; self.pending_clarification=False; self.pending_budget=None; self.history=[]
    def merge(self,slots,message):
        q=message.lower()
        if 'forget the budget' in q: self.filters.pop('price_min',None); self.filters.pop('price_max',None)
        if any(x in q for x in ('start over','new search')): self.filters={}
        for k,v in slots.to_dict().items():
            if k in ('category','brand','color','material','size','price_min','price_max') and v is not None: self.filters[k]=v
        return self.filters
    def resolve(self,message):
        import re
        if not self.pending_clarification or not self.last_candidates: return None
        q=message.lower().strip(); ordinals={'first':0,'1':0,'one':0,'second':1,'2':1,'two':1,'third':2,'3':2,'three':2,'fourth':3,'4':3}
        for word,i in ordinals.items():
            if q==word or q.startswith(word+' '): return self.last_candidates[i] if i<len(self.last_candidates) else None
        if 'cheapest' in q: return min(self.last_candidates,key=lambda c:c['product'].get('price') or float('inf'))
        if 'highest rated' in q or 'best rated' in q: return max(self.last_candidates,key=lambda c:c['product'].get('rating') or 0)
        m=__import__('re').search(r'\bp\d{5}\b',q,re.I)
        for c in self.last_candidates:
            p=c['product']
            if m and p['id'].lower()==m.group().lower(): return c
            if any(v.lower() in q for v in [p['title'],*p.get('attributes',{}).values()] if len(v)>2): return c
        return None
