import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.pipeline import Assistant

def main():
    if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(); p.add_argument('--debug',action='store_true'); a=p.parse_args(); bot=Assistant(); print('TrustCart demo. Type quit to exit.')
    while True:
        try:q=input('You: ').strip()
        except (EOFError,KeyboardInterrupt):break
        if q.lower() in ('quit','exit'):break
        r=bot.chat('cli',q); print('Assistant:',r.text)
        if a.debug: print('DEBUG',{'action':r.action,'slots':r.slots,'telemetry':r.telemetry,'reason':r.debug['reason'],'relaxed':r.debug['relaxed']})
if __name__=='__main__':main()
