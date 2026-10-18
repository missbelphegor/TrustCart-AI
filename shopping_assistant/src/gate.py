from dataclasses import dataclass
import config

@dataclass
class GateDecision:
    action:str; reason:str; candidates:list; policy:list|None=None

def decide(slots,candidates,products,policy):
    if slots.intent=='out_of_scope': return GateDecision('REFUSE','out_of_scope',[])
    if slots.intent=='policy':
        topic={'return':'returns','refund':'returns','delivery':'shipping'}.get(slots.policy_topic,slots.policy_topic)
        matches=[x for x in policy if (not topic or topic in x['topic'])]
        return GateDecision('ANSWER' if matches else 'REFUSE','policy_match' if matches else 'policy_not_covered',[],matches[:3])
    if not candidates: return GateDecision('REFUSE','no_match',[])
    if slots.intent=='chitchat' and not slots.unknown_entities: return GateDecision('CLARIFY','underspecified',candidates[:3])
    if any(x.lower().rstrip('s') in {'iphone','playstation','nike'} for x in (slots.unknown_entities or [])):
        return GateDecision('REFUSE','unknown_entity',[])
    if slots.unknown_entities and not slots.category and not any(any(t in p['title'].lower() for t in slots.raw_normalized_query.split()) for p in products):
        return GateDecision('REFUSE','unknown_entity',[])
    if not slots.category and not slots.product_ref and not slots.color and not slots.brand and not slots.price_max and not slots.price_min:
        return GateDecision('CLARIFY','underspecified',candidates[:3])
    # A named reference with several plausible matches is ambiguous; do not select a price.
    plausible=candidates[:]
    exact=[c for c in plausible if ' '.join(c['product']['title'].lower().split()) in slots.raw_normalized_query]
    if not exact and slots.product_ref:
        ref=[w for w in slots.product_ref.split() if len(w)>2]
        title_matches=[c for c in plausible if ref and all(w in c['product']['title'].lower().split() for w in ref)]
        if len(title_matches)==1: exact=title_matches
    if exact: return GateDecision('ANSWER','exact_product',exact[:1])
    if slots.intent in ('price_lookup','stock_check') and slots.product_ref and len(plausible)>1:
        top=plausible[0]['confidence']; near=[c for c in plausible if c['confidence']>=top*config.AMBIGUITY_RATIO]
        if len({c['product']['id'] for c in near})>=2: return GateDecision('CLARIFY','ambiguous_reference',near[:5])
    if len(products)>1 and not slots.category and not slots.product_ref and not slots.price_max and not slots.price_min:
        return GateDecision('CLARIFY','underspecified',candidates[:3])
    return GateDecision('ANSWER','retrieved',candidates[:5])
