import re

class VerificationResult:
    def __init__(self,valid,claims): self.valid=valid; self.claims=claims; self.precision=(sum(c['supported'] for c in claims)/len(claims) if claims else 1.0)

def verify(answer_text,source):
    products=source.get('products',[]); byid={p['id']:p for p in products}; policy={p['id']:p for p in source.get('policy',[])}; claims=[]
    attr_values={k:{str(p.get(k,'')).lower() for p in products if p.get(k) not in (None,'')} for k in ('brand','color','material','size','category')}
    for sentence in re.split(r'(?<=[.!?])\s+(?!\[)',answer_text):
        if not sentence.strip(): continue
        ids=re.findall(r'\[(P[^\]]+|POLICY:[^\]]+)\]',sentence)
        low=sentence.lower()
        attr_claim=any(re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',low) for vals in attr_values.values() for v in vals)
        title_claim=any(p['title'].lower() in low for p in products)
        factual=bool(re.search(r'₹|in stock|out of stock|rated|business days|delivery|returned|warranty|coverage|shipping fee|\d+\s+days',sentence,re.I)) or (not low.startswith('filters:') and (attr_claim or title_claim))
        # This reports the result of applying the user's filter, not a product fact.
        if low.startswith('no matching products were found'):
            factual=False
        ok=bool(ids) if factual else True
        for ident in ids:
            if ident.startswith('POLICY:'):
                ok &= ident in policy and policy[ident]['text'] in sentence
            elif ident in byid:
                p=byid[ident]
                for price in re.findall(r'₹([\d,]+)',sentence): ok &= int(price.replace(',',''))==int(p['price'] or -1)
                if 'in stock' in sentence.lower(): ok &= p['stock'] is True
                if 'out of stock' in sentence.lower(): ok &= p['stock'] is False
                if 'rated' in sentence.lower(): ok &= p['rating'] is not None and f"{p['rating']:.1f}/5" in sentence
                if not low.startswith('filters:'):
                    for field,values in attr_values.items():
                        if any(re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',low) for v in values):
                            stated=[v for v in values if re.search(r'(?<!\w)'+re.escape(v)+r'(?!\w)',low)]
                            ok &= not stated or str(p.get(field,'')).lower() in stated
            else: ok=False
        claims.append({'sentence':sentence,'supported':bool(ok),'ids':ids})
    return VerificationResult(all(c['supported'] for c in claims),claims)
