import re, unicodedata, difflib

HINDI={'sasta':'cheap','kapde':'clothes','joote':'shoes','jootein':'shoes','kitne ka':'price','kitna':'price','wapas':'return','nahi':'no','chahiye':'want','dikhao':'show','mehenga':'expensive','sabse sasta':'cheapest'}
DEV='०१२३४५६७८९'; ASCII='0123456789'
def normalize(q):
    q=unicodedata.normalize('NFKC',str(q)).translate(str.maketrans(DEV,ASCII)).lower()
    q=re.sub(r'[^\w₹.<>-]+',' ',q,flags=re.UNICODE); q=re.sub(r'\s+',' ',q).strip()
    for a,b in sorted(HINDI.items(),key=lambda x:-len(x[0])): q=re.sub(r'\b'+re.escape(a)+r'\b',b,q)
    return q

def parse_price(q):
    q=unicodedata.normalize('NFKC',str(q)).translate(str.maketrans(DEV,ASCII)).lower().replace(',','')
    q=re.sub(r'[^\w₹.<>-]+',' ',q); q=re.sub(r'\s+',' ',q).strip()
    def val(s):
        n=float(s.lower().removesuffix('k'))*(1000 if s.lower().endswith('k') else 1); return int(n)
    nums=r'(\d+(?:\.\d+)?k?)'
    m=re.search(r'between\s+'+nums+r'\s+(?:and|to)\s+'+nums,q)
    if not m: m=re.search(r'(?<!\w)'+nums+r'\s*-\s*'+nums,q)
    if m: return val(m.group(1)),val(m.group(2))
    m=re.search(r'(?:under|below|less than|max|upto|up to|tak|se kam|<)\s*(?:₹|rs\.?\s*|inr\s*|rupees?\s*)?'+nums,q)
    if m: return None,val(m.group(1))
    m=re.search(r'(?:above|over|at least|minimum)\s*(?:₹|rs\.?\s*|inr\s*|rupees?\s*)?'+nums,q)
    if m: return val(m.group(1)),None
    m=re.search(r'(?:₹\s*|rs\.?\s*|inr\s*|rupees?\s*)'+nums,q)
    if m: n=val(m.group(1)); return n,n
    return None,None

def fuzzy(value, vocab, threshold=.84):
    s=value.lower()
    if s in vocab:return s
    match=difflib.get_close_matches(s,vocab,n=1,cutoff=threshold)
    return match[0] if match else None
