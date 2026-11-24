import unittest,tempfile,os,json
import server
class TestPortal(unittest.TestCase):
 def test_exact_and_related(self):
  self.assertEqual(server.score('An AI Study','an ai study'),1)
  self.assertGreater(server.score('Deep Learning for Health','Deep Learning for Healthcare'),.7)
  self.assertLess(server.score('Satellite Networks','Plant Disease Recognition'),.6)
 def test_seed_and_matches(self):
  with tempfile.TemporaryDirectory() as d:
   old=server.DB;server.DB=os.path.join(d,'test.sqlite3')
   try:
    server.init()
    with server.connect() as c:
     self.assertEqual(c.execute('select count(*) from papers').fetchone()[0],len(json.load(open(os.path.join(server.ROOT,'seed_records.json')))))
     title=c.execute('select title from papers limit 1').fetchone()[0]
     self.assertEqual(server.matches(c,title)[0]['similarity'],1)
   finally:server.DB=old
if __name__=='__main__':unittest.main()
