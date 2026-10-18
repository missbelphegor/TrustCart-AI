def money(v):
    n=int(round(v)); s=str(n)
    if len(s)>3: s=s[:-3]+''.join(','+s[max(0,len(s)-3-i*2):len(s)-1-i*2] for i in range((len(s)-4)//2+1,-1,-1)) if False else s
    # Indian grouping: last three digits, then pairs.
    if len(str(n))>3:
        raw=str(n); s=raw[-3:]; raw=raw[:-3]
        while raw: s=raw[-2:]+','+s; raw=raw[:-2]
    return '₹'+s

def build(decision,slots,relaxed=()):
    if decision.action=='REFUSE':
        if decision.reason=='unknown_entity': return f"I couldn't find {slots.product_ref or 'that item'} in our catalogue, so I can't tell you that."
        if decision.reason=='out_of_scope': return 'I cannot access order, account, or payment information.'
        if decision.reason=='policy_not_covered': return "I couldn't find that information in the available policy."
        return 'I could not find a supported match in this catalogue.'
    if decision.action=='CLARIFY':
        return 'Which one do you mean? ' + ' '.join(f"{c['product']['title']}, {money(c['product']['price'])} [{c['product']['id'] }]." for c in decision.candidates)
    if decision.policy:
        import re
        return ' '.join(f"{sentence.strip()} [{x['id']}]" for x in decision.policy for sentence in re.split(r'(?<=[.!?])\s+(?!\[)',x['text']) if sentence.strip())
    prefix='';
    if relaxed: prefix='I relaxed '+', '.join(k.replace('_',' ') for k,v in relaxed)+'. '
    products=decision.candidates
    if slots.sort=='cheapest': products=sorted(products,key=lambda c:c['product']['price'] or float('inf'))
    if slots.sort=='best_rated': products=sorted(products,key=lambda c:c['product']['rating'] or 0,reverse=True)
    out=[]
    for c in products:
        p=c['product']; facts=[p['title']]
        if p['price'] is not None: facts.append(money(p['price']))
        if p['stock'] is not None: facts.append('in stock' if p['stock'] else 'out of stock')
        if p['rating'] is not None: facts.append(f"rated {p['rating']:.1f}/5")
        out.append(f"{', '.join(facts)} [{p['id']}].")
    return prefix+' '.join(out)
