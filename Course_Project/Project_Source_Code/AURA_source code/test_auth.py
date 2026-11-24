import unittest,tempfile,os,secrets,sqlite3
import server
class AuthTests(unittest.TestCase):
 def test_password_hash_salted_and_distinct(self):
  a=secrets.token_hex(16);b=secrets.token_hex(16)
  self.assertEqual(server.hash_password('strong-password-123',a),server.hash_password('strong-password-123',a))
  self.assertNotEqual(server.hash_password('strong-password-123',a),server.hash_password('wrong-password-123',a))
  self.assertNotEqual(server.hash_password('strong-password-123',a),server.hash_password('strong-password-123',b))
 def test_auth_without_cookie_refused(self):
  with tempfile.TemporaryDirectory() as d:
   old=server.DB;server.DB=os.path.join(d,'auth.sqlite3')
   try:
    server.init()
    class Request:headers={}
    with server.connect() as c:self.assertIsNone(server.reviewer_from_request(Request(),c))
   finally:server.DB=old
if __name__=='__main__':unittest.main()
