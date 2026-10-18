"""Optional LLM placeholder. The default system deliberately makes zero LLM calls."""
class LocalLLM:
    def __init__(self,*args,**kwargs): self.calls=0
    def parse(self,query): return None
