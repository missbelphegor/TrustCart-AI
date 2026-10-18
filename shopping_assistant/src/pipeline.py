from dataclasses import dataclass
import time, uuid
from . import ingest,index,understand,retrieve,gate,answer,verifier,telemetry
import config

@dataclass
class Response:
    text:str; action:str; citations:list; slots:dict; telemetry:dict; debug:dict

class Assistant:
    def __init__(self,catalog_path=None,policy_path=None):
        self.products,self.vocab,self.issues=ingest.load_catalog(catalog_path or config.CATALOG_PATH)
        self.policy=ingest.load_policy(policy_path or config.POLICY_PATH); self.index=index.build_index(self.products,self.policy)
        self.sessions={}
    def chat(self,session_id,message):
        t=time.perf_counter(); slots=understand.understand(message,self.vocab); t1=time.perf_counter()
        sess=self.sessions.setdefault(session_id,__import__('src.session',fromlist=['Session']).Session()); filters=sess.merge(slots,message)
        for k,v in filters.items(): setattr(slots,k,v)
        reply=message.strip().lower()
        yes=bool(re.match(r'^(yes|yeah|yep|sure|okay|ok|please do|go ahead|increase\b|show alternatives\b)',reply))
        no=bool(re.match(r'^(no|nope|nah|not now|keep the budget\b)',reply))
        budget_reply=bool(sess.pending_budget and (yes or no))
        if budget_reply and yes:
            found=sess.pending_budget['candidates']; relaxed=[]; decision=gate.GateDecision('ANSWER','budget_increased',found)
            sess.pending_budget=None
        elif budget_reply and no:
            found=[]; relaxed=[]; decision=gate.GateDecision('REFUSE','budget_declined',[])
            sess.pending_budget=None
        else:
            if sess.pending_budget: sess.pending_budget=None
            selected=sess.resolve(message)
            if selected:
                from .gate import GateDecision
                found=[selected]; relaxed=[]; decision=GateDecision('ANSWER','clarification_resolved',found); sess.pending_clarification=False
            else:
                found,relaxed=retrieve.retrieve(self.products,self.index,slots); decision=gate.decide(slots,found,self.products,self.policy)
                if not found and slots.price_max is not None and slots.intent in ('product_search','price_lookup'):
                    alternatives,_=retrieve.retrieve(self.products,self.index,slots,ignore_price_max=True)
                    alternatives=[c for c in alternatives if c['product'].get('price') is not None and c['product']['price']>slots.price_max]
                    if alternatives:
                        sess.pending_budget={'candidates':alternatives,'maximum':slots.price_max}
                        decision=gate.GateDecision('BUDGET_CONFIRM','budget_no_match',[])
        t2=time.perf_counter(); t3=time.perf_counter()
        if decision.action=='BUDGET_CONFIRM':
            text=f"No matching products were found under {answer.money(slots.price_max)}. Would you like to increase your budget to see higher-priced alternatives?"
        elif decision.reason=='budget_declined':
            text=f"No matching products were found under {answer.money(filters.get('price_max'))}. I’ll keep your budget unchanged."
        elif decision.reason=='budget_increased':
            display_slots=understand.Slots(**slots.to_dict()); display_slots.price_max=None
            text='Here are higher-priced alternatives. Their listed prices are above your previous budget. '+answer.build(decision,display_slots)
        else:
            text=answer.build(decision,slots,relaxed)
        active=[]
        labels={'category':'category','brand':'brand','color':'color','material':'material','size':'size'}
        for k,label in labels.items():
            if filters.get(k): active.append(str(filters[k]))
        if filters.get('price_min') is not None: active.append(f"over {filters['price_min']}")
        if filters.get('price_max') is not None: active.append(f"under {filters['price_max']}")
        if active and decision.action not in ('REFUSE','BUDGET_CONFIRM') and decision.reason!='budget_increased': text='Filters: '+', '.join(active)+'. '+text
        result=verifier.verify(text,{'products':self.products,'policy':self.policy}); rescue=False
        if not result.valid:
            rescue=True
            # Pure safe refusal avoids serving unverifiable template output.
            text='I could not provide a verified answer from the available catalogue.'; decision.action='REFUSE'; result=verifier.verify(text,{'products':self.products,'policy':self.policy})
        t4=time.perf_counter(); citations=re.findall(r'\[([^\]]+)\]',text)
        row={'query_id':str(uuid.uuid4()),'query':message,'t_normalize':(t1-t)*1000,'t_llm_parse':0,'t_retrieve':(t2-t1)*1000,'t_gate':(t3-t2)*1000,'t_generate':0,'t_verify':(t4-t3)*1000,'t_total':(t4-t)*1000,'tokens_in':0,'tokens_out':0,'llm_calls':0,'llm_skipped':True,'action':decision.action,'verifier_rescue':rescue}
        telemetry.log(row); sess.last_candidates=decision.candidates; sess.pending_clarification=decision.action=='CLARIFY'; sess.history.append((message,text))
        return Response(text,decision.action,citations,slots.to_dict(),row,{'reason':decision.reason,'relaxed':relaxed,'candidates':decision.candidates,'verifier':result.claims,'active_filters':filters})

import re
