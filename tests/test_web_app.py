import os,tempfile,unittest
from pathlib import Path
_TMP=tempfile.TemporaryDirectory()
os.environ["TAPRI_SECRET_KEY"]="test-secret-key-with-more-than-32-characters"
os.environ["TAPRI_ADMIN_PIN"]="test-password-123"
os.environ["TAPRI_DB_PATH"]=str(Path(_TMP.name)/"test.sqlite3")
import web_app
class TrackerWebTests(unittest.TestCase):
 def setUp(self):
  web_app.app.config.update(TESTING=True)
  with web_app.connect() as db:
   db.execute("DELETE FROM recoveries"); db.execute("DELETE FROM orders"); db.execute("DELETE FROM attempts")
  self.client=web_app.app.test_client()
 def token(self):
  with self.client.session_transaction() as s: return s["csrf"]
 def login(self):
  self.client.get("/login")
  return self.client.post("/login",data={"csrf":self.token(),"password":"test-password-123"},follow_redirects=True)
 def test_requires_login(self): self.assertEqual(self.client.get("/").status_code,302)
 def test_order_and_recovery(self):
  self.assertEqual(self.login().status_code,200)
  r=self.client.post("/orders",data={"csrf":self.token(),"item":"Tea","price":"10","served":"3","paid":"2","method":"upi","crowd":"high"})
  self.assertEqual(r.status_code,302); oid=int(r.location.rsplit("/",1)[1])
  self.assertEqual(self.client.get(f"/orders/{oid}").status_code,200)
  self.client.post(f"/orders/{oid}/recover",data={"csrf":self.token(),"amount":"5","method":"cash"})
  self.assertIn("₹5",self.client.get(f"/orders/{oid}").get_data(as_text=True))
 def test_over_recovery_rejected(self):
  self.login()
  self.client.post("/orders",data={"csrf":self.token(),"item":"Tea","price":"10","served":"2","paid":"1","method":"cash","crowd":"low"})
  with web_app.connect() as db: oid=db.execute("SELECT MAX(id) FROM orders").fetchone()[0]
  r=self.client.post(f"/orders/{oid}/recover",data={"csrf":self.token(),"amount":"20","method":"upi"},follow_redirects=True)
  self.assertIn("cannot exceed",r.get_data(as_text=True))
 def test_csrf_required(self):
  self.login(); self.assertEqual(self.client.post("/orders",data={"item":"Tea"}).status_code,400)
 def test_invalid_quantity_not_saved(self):
  self.login()
  self.client.post("/orders",data={"csrf":self.token(),"item":"Tea","price":"10","served":"1","paid":"2","method":"cash","crowd":"low"},follow_redirects=True)
  with web_app.connect() as db: self.assertEqual(db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],0)
 def test_logout(self):
  self.login(); self.client.post("/logout",data={"csrf":self.token()})
  self.assertEqual(self.client.get("/").status_code,302)
if __name__=="__main__": unittest.main()
