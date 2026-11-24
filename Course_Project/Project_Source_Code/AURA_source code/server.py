import os,json,sqlite3,datetime,hashlib,re,difflib,csv,io,threading,secrets,hmac,time
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
ROOT=os.path.dirname(os.path.abspath(__file__));DB=os.path.join(ROOT,'aura.sqlite3')
FIELDS=['faculty','phone','authors','title','conference','quartile','level','year','category','registration','ta','da','total','doi','department','email','submission_date','status','source','submitted_by','reviewer','review_note','reviewed_at','source_details']
def connect():
 c=sqlite3.connect(DB,timeout=15);c.row_factory=sqlite3.Row;return c
def now():return datetime.datetime.now().isoformat(timespec='seconds')
def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',str(s or '').lower()))
def score(a,b):
 a,b=norm(a),norm(b)
 if not a or not b:return 0
 if a==b:return 1
 aa=set(a.split());bb=set(b.split());j=len(aa&bb)/max(1,len(aa|bb));seq=difflib.SequenceMatcher(None,a,b).ratio();return round(.52*seq+.48*j,3)
def matches(c,title,exclude=None):
 rows=c.execute('SELECT id,title,faculty,conference,status,source FROM papers WHERE title IS NOT NULL').fetchall()
 out=[dict(r,similarity=score(title,r['title'])) for r in rows if r['id']!=exclude and score(title,r['title'])>=.58]
 return sorted(out,key=lambda x:-x['similarity'])[:8]
def audit(c,action,paper_id,actor,detail):c.execute('INSERT INTO audit(at,action,paper_id,actor,detail) VALUES(?,?,?,?,?)',(now(),action,paper_id,actor,json.dumps(detail,ensure_ascii=False)))
def init():
 with connect() as c:
  c.execute('CREATE TABLE IF NOT EXISTS papers(id INTEGER PRIMARY KEY AUTOINCREMENT,'+','.join(x+' TEXT' for x in FIELDS)+',created_at TEXT NOT NULL,updated_at TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS reviewers(username TEXT PRIMARY KEY,full_name TEXT NOT NULL,role TEXT NOT NULL,salt TEXT NOT NULL,password_hash TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,username TEXT NOT NULL,expires INTEGER NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,action TEXT,paper_id INTEGER,actor TEXT,detail TEXT)')
  # Safe schema migration for databases created by earlier AURA versions.
  existing={row[1] for row in c.execute('PRAGMA table_info(papers)').fetchall()}
  if 'source_details' not in existing:
   c.execute('ALTER TABLE papers ADD COLUMN source_details TEXT')
  if not c.execute('SELECT count(*) FROM papers').fetchone()[0]:
   seed=json.load(open(os.path.join(ROOT,'seed_records.json'),encoding='utf-8'))
   for r in seed:
    d={**r,'status':'Imported · Unverified','source':r.get('source') or 'Authority spreadsheet · 2024–2026','submission_date':'','submitted_by':'Authority import'}
    c.execute('INSERT INTO papers('+','.join(FIELDS)+',created_at,updated_at) VALUES('+','.join('?' for _ in range(len(FIELDS)+2))+')',[str(d.get(f,'') or '') for f in FIELDS]+[now(),now()])
   audit(c,'IMPORT',None,'System',{'count':len(seed),'source':'Authority spreadsheets · 2024–2026'})
def hash_password(password,salt):
 return hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),260000).hex()
def reviewer_from_request(handler,c):
 cookies=handler.headers.get('Cookie','').split(';')
 token=next((x.strip()[13:] for x in cookies if x.strip().startswith('aura_session=')),'')
 if not token:return None
 digest=hashlib.sha256(token.encode()).hexdigest()
 row=c.execute('SELECT r.username,r.full_name,r.role FROM sessions s JOIN reviewers r ON r.username=s.username WHERE s.token_hash=? AND s.expires>?',(digest,int(time.time()))).fetchone()
 return dict(row) if row else None
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def respond(self,data,status=200,typ='application/json'):
  raw=(json.dumps(data,ensure_ascii=False,default=str) if typ=='application/json' else data).encode('utf-8');self.send_response(status);self.send_header('Content-Type',typ+'; charset=utf-8');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
 def session_cookie(self,token,maxage):
  self.send_header('Set-Cookie',f'aura_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={maxage}')
 def body(self):
  n=int(self.headers.get('Content-Length','0'))
  if n>1000000:raise ValueError('Request too large')
  return json.loads(self.rfile.read(n) or b'{}')
 def do_GET(self):
  path=urlparse(self.path).path;q=parse_qs(urlparse(self.path).query)
  if path in ('/','/index.html'):
   return self.respond(open(os.path.join(ROOT,'index.html'),encoding='utf-8').read(),typ='text/html')
  if path=='/api/context':
   with connect() as c:
    rows=[dict(r) for r in c.execute('SELECT * FROM papers ORDER BY id DESC')];user=reviewer_from_request(self,c);log=[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY id DESC LIMIT 100')] if user else []
   return self.respond({'papers':rows,'audit':log,'reviewer':user,'mode':'LOCAL · AUTHORITY IMPORT UNVERIFIED'})
  if path=='/api/intelligence':
   from intelligence import intelligence_payload
   return self.respond(intelligence_payload())
  if path=='/api/nirf-naac-report':
   from intelligence import report_csv
   with connect() as c:
    user=reviewer_from_request(self,c)
    if not user:return self.respond({'error':'Reviewer login required'},401)
    if user['role'] not in ('HOD','Dean','Research Office'):return self.respond({'error':'Research Office / HoD / Dean access required'},403)
   rows=report_csv();o=io.StringIO();fields=['faculty','department','verified_publications','verified_citations','h_index','source_names','source_record_urls','approved_by','approved_at','workflow_run'];w=csv.DictWriter(o,fieldnames=fields);w.writeheader();w.writerows(rows)
   data=o.getvalue().encode('utf-8-sig');self.send_response(200);self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename= AURA_NIRF_NAAC_approved_report.csv');self.send_header('Content-Length',str(len(data)));self.end_headers();return self.wfile.write(data)
  if path=='/api/check':
   title=q.get('title',[''])[0]
   with connect() as c:res=matches(c,title)
   return self.respond({'matches':res,'threshold':.82,'blocking':any(x['similarity']>=.82 for x in res)})
  if path=='/api/export':
   with connect() as c:
    if not reviewer_from_request(self,c):return self.respond({'error':'Reviewer login required for export'},401)
    rows=[dict(r) for r in c.execute('SELECT * FROM papers ORDER BY id')]
   o=io.StringIO();writer=csv.DictWriter(o,fieldnames=['id']+FIELDS+['created_at','updated_at']);writer.writeheader();writer.writerows(rows)
   self.send_response(200);data=o.getvalue().encode('utf-8-sig');self.send_header('Content-Type','text/csv; charset=utf-8');self.send_header('Content-Disposition','attachment; filename="AURA_registry.csv"');self.send_header('Content-Length',str(len(data)));self.end_headers();return self.wfile.write(data)
  return self.respond({'error':'Not found'},404)
 def do_POST(self):
  try:
   path=urlparse(self.path).path;d=self.body()
   with connect() as c:
    if path=='/api/login':
     username=str(d.get('username','')).strip().lower();password=str(d.get('password',''))
     row=c.execute('SELECT * FROM reviewers WHERE username=?',(username,)).fetchone()
     if not row or not hmac.compare_digest(hash_password(password,row['salt']),row['password_hash']):return self.respond({'error':'Invalid reviewer ID or password'},401)
     token=secrets.token_urlsafe(32);digest=hashlib.sha256(token.encode()).hexdigest()
     c.execute('INSERT INTO sessions VALUES(?,?,?)',(digest,username,int(time.time())+28800))
     audit(c,'LOGIN',None,username,{'role':row['role']})
     data=json.dumps({'ok':True,'reviewer':{'username':username,'full_name':row['full_name'],'role':row['role']}}).encode()
     self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.session_cookie(token,28800);self.end_headers();return self.wfile.write(data)
    if path=='/api/logout':
     cookies=self.headers.get('Cookie','').split(';');token=next((x.strip()[13:] for x in cookies if x.strip().startswith('aura_session=')),'')
     if token:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
     data=b'{"ok":true}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.session_cookie('',0);self.end_headers();return self.wfile.write(data)
    if path=='/api/faculty-profile':
     from intelligence import create_profile
     pid=create_profile(d);return self.respond({'ok':True,'id':pid})
    if path=='/api/citation-record':
     from intelligence import add_citation
     cid=add_citation(d);return self.respond({'ok':True,'id':cid})
    if path=='/api/workflow/run':
     from intelligence import run_workflow
     result=run_workflow(int(d.get('faculty_id') or 0));return self.respond({'ok':True,**result})
    if path=='/api/workflow/approve':
     user=reviewer_from_request(self,c)
     if not user:return self.respond({'error':'Reviewer login required'},401)
     from intelligence import approve_run
     approve_run(int(d.get('run_id') or 0),user);return self.respond({'ok':True})
    if path=='/api/duplicate/resolve':
     user=reviewer_from_request(self,c)
     if not user:return self.respond({'error':'Reviewer login required'},401)
     from intelligence import resolve_duplicate
     resolve_duplicate(int(d.get('primary_id') or 0),int(d.get('duplicate_id') or 0),user);return self.respond({'ok':True})
    if path=='/api/citation/verify':
     user=reviewer_from_request(self,c)
     if not user:return self.respond({'error':'Reviewer login required'},401)
     if user['role'] not in ('HOD','Dean','Research Office'):return self.respond({'error':'Research Office / HoD / Dean access required'},403)
     cid=int(d.get('id') or 0);url=str(d.get('source_url','')).strip();note=str(d.get('notes','')).strip()
     if not url:return self.respond({'error':'A source URL is required for verification'},400)
     row=c.execute('SELECT * FROM citation_records WHERE id=?',(cid,)).fetchone()
     if not row:return self.respond({'error':'Citation record not found'},404)
     c.execute("UPDATE citation_records SET verification_status='Verified',source_url=? WHERE id=?",(url,cid))
     c.execute('INSERT INTO source_verifications(paper_id,source,indexing_status,source_url,checked_at,checked_by,notes) VALUES(?,?,?,?,?,?,?)',(None,row['source'],'Verified',url,now(),user['full_name'],note))
     audit(c,'CITATION_VERIFIED',None,user['full_name'],{'citation_id':cid,'source':row['source'],'source_url':url});return self.respond({'ok':True})
    if path=='/api/submit':
     for f in ['faculty','authors','title','conference','year','category','submitted_by']:
      if not str(d.get(f,'')).strip():return self.respond({'error':f.replace('_',' ').title()+' is required'},400)
     if not re.fullmatch(r'20\d\d',str(d['year'])):return self.respond({'error':'Enter a valid four-digit year (20xx)'},400)
     hit=matches(c,d['title']);blocking=[x for x in hit if x['similarity']>=.82]
     if blocking and not (d.get('override_reason','').strip() and d.get('acknowledge_duplicate') is True):return self.respond({'error':'Potential duplicate requires explicit acknowledgement and a written justification','matches':blocking},409)
     values={f:str(d.get(f,'') or '').strip() for f in FIELDS};values.update(status='Pending Review',source='New submission · Not verified',submission_date=now()[:10])
     c.execute('INSERT INTO papers('+','.join(FIELDS)+',created_at,updated_at) VALUES('+','.join('?' for _ in range(len(FIELDS)+2))+')',[values[f] for f in FIELDS]+[now(),now()]);pid=c.execute('SELECT last_insert_rowid()').fetchone()[0]
     audit(c,'SUBMITTED',pid,values['submitted_by'],{'title':values['title'],'duplicate_override':d.get('override_reason',''),'similar_matches':len(hit)})
     return self.respond({'ok':True,'id':pid,'matches':hit})
    if path=='/api/decide':
     user=reviewer_from_request(self,c)
     if not user:return self.respond({'error':'Reviewer login required'},401)
     pid=int(d.get('id',0));role=user['role'];name=user['full_name'];decision=str(d.get('decision',''));note=str(d.get('note','')).strip()
     if role not in ('HOD','Dean','Research Office'):return self.respond({'error':'Insufficient permissions'},403)

     if decision not in ('Approved','Returned') or not note:return self.respond({'error':'Decision and review note required'},400)
     paper=c.execute('SELECT * FROM papers WHERE id=?',(pid,)).fetchone()
     if not paper:return self.respond({'error':'Paper not found'},404)
     if paper['status']!='Pending Review':return self.respond({'error':'Only pending submissions can be decided; imported records require independent verification'},409)
     c.execute('UPDATE papers SET status=?,reviewer=?,review_note=?,reviewed_at=?,updated_at=? WHERE id=?',(decision,name+' · '+role,note,now(),now(),pid));audit(c,'DECISION',pid,name,{'role':role,'decision':decision,'note':note});return self.respond({'ok':True})
   return self.respond({'error':'Unknown endpoint'},404)
  except (ValueError,TypeError,json.JSONDecodeError) as e:return self.respond({'error':str(e)},400)
  except Exception as e:return self.respond({'error':'Internal server error'},500)
if __name__=='__main__':
 init();
 from intelligence import ensure_tables
 ensure_tables();port=int(os.environ.get('AURA_PORT','8765'));print(f'AURA ready: http://localhost:{port}',flush=True);ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
