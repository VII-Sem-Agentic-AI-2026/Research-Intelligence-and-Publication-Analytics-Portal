import os,tempfile,unittest,json
import server,replace_authority_data

class RefreshTests(unittest.TestCase):
    def test_seed_has_three_year_sources_and_titles(self):
        with open(os.path.join(server.ROOT,'seed_records.json'),encoding='utf-8') as f:
            rows=json.load(f)
        self.assertEqual(len(rows),553)
        counts={}
        for r in rows: counts[r['source']]=counts.get(r['source'],0)+1
        self.assertEqual(counts['Authority spreadsheet · 2024'],161)
        self.assertEqual(counts['Authority spreadsheet · 2025'],254)
        self.assertEqual(counts['Authority spreadsheet · 2026'],138)
        self.assertTrue(all(r.get('title') for r in rows))
    def test_refresh_preserves_new_submissions_and_replaces_imports(self):
        old=server.DB
        with tempfile.TemporaryDirectory() as d:
            server.DB=os.path.join(d,'test.sqlite3')
            try:
                server.init()
                with server.connect() as c:
                    c.execute("INSERT INTO papers(title,faculty,authors,conference,year,category,submitted_by,status,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        ('A new original paper','Faculty A','Author A','Conference A','2026','REU','Faculty A','Pending Review','New submission · Not verified',server.now(),server.now()))
                    c.execute("INSERT INTO reviewers(username,full_name,role,salt,password_hash) VALUES(?,?,?,?,?)",
                        ('test','Test Reviewer','Research Office','00'*16,'hash'))
                replace_authority_data.refresh()
                with server.connect() as c:
                    imported=c.execute("SELECT COUNT(*) FROM papers WHERE status='Imported · Unverified'").fetchone()[0]
                    new=c.execute("SELECT COUNT(*) FROM papers WHERE status='Pending Review'").fetchone()[0]
                    reviewer=c.execute("SELECT COUNT(*) FROM reviewers WHERE username='test'").fetchone()[0]
                    self.assertEqual(imported,553)
                    self.assertEqual(new,1)
                    self.assertEqual(reviewer,1)
            finally:
                server.DB=old

if __name__=='__main__': unittest.main()
