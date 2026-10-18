import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.normalize import parse_price,normalize,fuzzy
from src.pipeline import Assistant
from src.answer import money
from src.verifier import verify
from src.retrieve import rrf

class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.bot=Assistant()
 def test_prices(self):
  self.assertEqual(parse_price('under 2k'),(None,2000)); self.assertEqual(parse_price('below rs 2,000'),(None,2000)); self.assertEqual(parse_price('between 500 and 1.5k'),(500,1500)); self.assertEqual(parse_price('over ₹1500'),(1500,None)); self.assertEqual(parse_price('rs 1500'),(1500,1500))
 def test_hinglish(self): self.assertIn('cheap',normalize('sasta kapde dikhao'))
 def test_typo(self): self.assertEqual(self.bot.chat('typo','price of runing shoe').action,'CLARIFY')
 def test_fuzzy_guard(self): self.assertIsNone(fuzzy('iphone',['shirt','shoes'],.84))
 def test_rrf(self): self.assertEqual(rrf([1,2],[2,3])[0],2)
 def test_answers_refusals(self):
  self.assertEqual(self.bot.chat('t','do you sell iPhones?').action,'REFUSE'); self.assertEqual(self.bot.chat('t','where is my order').action,'REFUSE'); self.assertEqual(self.bot.chat('t','return policy').action,'ANSWER')
 def test_trap(self): self.assertEqual(self.bot.chat('trap','price of the blue running shoe').action,'CLARIFY')
 def test_verifier(self):
  p=self.bot.products[0]; src={'products':self.bot.products,'policy':self.bot.policy}
  self.assertFalse(verify(f"Blue Runner Pro ₹1 [P00001].",src).valid); self.assertFalse(verify('Blue Runner Pro ₹1,499.',src).valid); self.assertFalse(verify('Thing ₹10 [P99999].',src).valid)
 def test_money(self): self.assertEqual(money(125000),'₹1,25,000')
 def test_multiturn(self):
  b=Assistant(); first=b.chat('s','show me shirts'); b.chat('s','cotton only'); r=b.chat('s','under ₹2,000, and I already said cotton'); self.assertEqual(first.slots['category'],'Clothing'); self.assertEqual(r.slots['category'],'Clothing'); self.assertEqual(r.slots['material'],'cotton'); self.assertLessEqual(r.slots['price_max'],2000); self.assertIn('Filters:',r.text)
 def test_budget_never_relaxes_without_consent(self):
  b=Assistant(); r=b.chat('budget','Shoes under ₹500')
  self.assertEqual(r.action,'BUDGET_CONFIRM'); self.assertIn('No matching products were found',r.text); self.assertIn('increase your budget',r.text)
  self.assertFalse(r.citations); self.assertEqual(r.debug['relaxed'],[])
 def test_budget_alternatives_require_and_record_consent(self):
  b=Assistant(); ask=b.chat('budget-yes','Shoes under ₹500'); r=b.chat('budget-yes','Yes, please increase it')
  self.assertEqual(ask.action,'BUDGET_CONFIRM'); self.assertEqual(r.action,'ANSWER')
  self.assertIn('higher-priced alternatives',r.text); self.assertTrue(r.citations)
  self.assertIn('₹1,299',r.text); self.assertIn('₹1,499',r.text); self.assertIn('out of stock',r.text)
 def test_budget_decline_does_not_show_alternatives(self):
  b=Assistant(); b.chat('budget-no','Shoes under ₹500'); r=b.chat('budget-no','no')
  self.assertEqual(r.action,'REFUSE'); self.assertIn('No matching products were found',r.text)
  self.assertNotIn('₹1,299',r.text); self.assertFalse(r.citations)
 def test_clarification_reply(self):
  b=Assistant(); q=b.chat('pick','price of the blue running shoe'); self.assertEqual(q.action,'CLARIFY'); r=b.chat('pick','second one'); self.assertEqual(r.action,'ANSWER'); self.assertTrue(r.citations)
 def test_e2e_20(self):
  qs=['price of Blue Runner Pro','is Blue Runner Pro in stock','return policy','shipping time','warranty','show me shirts','cotton shirt under 2k','blue cotton shirt','do you sell iPhones','where is my order']*2
  for i,q in enumerate(qs): self.assertIsNotNone(self.bot.chat(f'e{i}',q).text)
if __name__=='__main__':unittest.main()
