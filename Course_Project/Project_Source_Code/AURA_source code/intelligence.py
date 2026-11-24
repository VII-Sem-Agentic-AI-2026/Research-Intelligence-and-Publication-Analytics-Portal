"""AURA research-intelligence agents and licensed-source connector readiness.

The adapters deliberately do not scrape websites. Real provider API calls require
institution-approved credentials/licences and are enabled through environment config.
"""
import os, json, datetime, re
from server import connect, now, audit, matches

AGENTS = [
    ('Faculty Profile Agent', 'Normalizes faculty identity, department, profile links and consent.'),
    ('Google Scholar Harvest Agent', 'Harvests publications/citations from a consented linked profile when an approved connector is configured.'),
    ('Scopus/WoS Verification Agent', 'Cross-checks indexing and metadata through licensed Scopus and Web of Science APIs.'),
    ('Duplicate Detection Agent', 'Flags cross-source duplicates and proposes reviewer-confirmed merges.'),
    ('Citation Analytics Agent', 'Calculates h-index, citation totals and year-wise trends from verified records.'),
    ('Dashboard Agent', 'Prepares dashboard and NIRF/NAAC export artifacts after approval.'),
    ('Validation Agent', 'Checks consent, provenance, completeness and consistency before human review.'),
]

def connector_status():
    return {
        'Google Scholar': {'configured': bool(os.getenv('AURA_SCHOLAR_ADAPTER_URL')), 'mode': 'Approved adapter endpoint' if os.getenv('AURA_SCHOLAR_ADAPTER_URL') else 'Not configured — no scraping performed'},
        'Scopus': {'configured': bool(os.getenv('SCOPUS_API_KEY')), 'mode': 'Elsevier API key configured' if os.getenv('SCOPUS_API_KEY') else 'API key/licence required'},
        'Web of Science': {'configured': bool(os.getenv('WOS_API_KEY')), 'mode': 'Clarivate API key configured' if os.getenv('WOS_API_KEY') else 'API key/licence required'},
    }

def ensure_tables():
    with connect() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS faculty_profiles(
          id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, email TEXT,
          department TEXT NOT NULL, scholar_url TEXT, scopus_id TEXT, wos_id TEXT,
          consent_scholar INTEGER NOT NULL DEFAULT 0, consent_scopus INTEGER NOT NULL DEFAULT 0,
          consent_wos INTEGER NOT NULL DEFAULT 0, consent_at TEXT, created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS citation_records(
          id INTEGER PRIMARY KEY AUTOINCREMENT, faculty_id INTEGER NOT NULL,
          paper_title TEXT NOT NULL, doi TEXT, publication_year TEXT, citations INTEGER NOT NULL DEFAULT 0,
          source TEXT NOT NULL, source_url TEXT, retrieved_at TEXT NOT NULL,
          verification_status TEXT NOT NULL DEFAULT 'Pending Verification',
          FOREIGN KEY(faculty_id) REFERENCES faculty_profiles(id))''')
        cols={x[1] for x in c.execute('PRAGMA table_info(citation_records)').fetchall()}
        if 'merged_into' not in cols: c.execute('ALTER TABLE citation_records ADD COLUMN merged_into INTEGER')
        c.execute('''CREATE TABLE IF NOT EXISTS workflow_runs(
          id INTEGER PRIMARY KEY AUTOINCREMENT, faculty_id INTEGER NOT NULL, status TEXT NOT NULL,
          started_at TEXT NOT NULL, completed_at TEXT, output TEXT NOT NULL,
          approved_by TEXT, approved_at TEXT, FOREIGN KEY(faculty_id) REFERENCES faculty_profiles(id))''')
        c.execute('''CREATE TABLE IF NOT EXISTS source_verifications(
          id INTEGER PRIMARY KEY AUTOINCREMENT, paper_id INTEGER, source TEXT NOT NULL,
          indexing_status TEXT NOT NULL, source_url TEXT, checked_at TEXT NOT NULL,
          checked_by TEXT NOT NULL, notes TEXT)''')

def profile_payload(c):
    return [dict(x) for x in c.execute('SELECT * FROM faculty_profiles ORDER BY full_name').fetchall()]

def intelligence_payload():
    ensure_tables()
    with connect() as c:
        profiles=profile_payload(c)
        runs=[dict(x) for x in c.execute('SELECT id,faculty_id,status,started_at,completed_at,approved_by,approved_at FROM workflow_runs ORDER BY id DESC LIMIT 30')]
        citations=[dict(x) for x in c.execute('SELECT cr.*, fp.full_name FROM citation_records cr JOIN faculty_profiles fp ON fp.id=cr.faculty_id ORDER BY cr.id DESC')]
        verifications=[dict(x) for x in c.execute('SELECT * FROM source_verifications ORDER BY id DESC LIMIT 50')]
    return {'profiles':profiles,'runs':runs,'citations':citations,'verifications':verifications,'agents':[{'name':n,'role':r} for n,r in AGENTS],'connectors':connector_status()}

def create_profile(d):
    ensure_tables()
    name=str(d.get('full_name','')).strip(); dept=str(d.get('department','')).strip(); email=str(d.get('email','')).strip()
    if not name or not dept: raise ValueError('Faculty name and department are required')
    flags=[bool(d.get('consent_scholar')),bool(d.get('consent_scopus')),bool(d.get('consent_wos'))]
    if any(flags) and not str(d.get('consent_confirmed',''))=='yes': raise ValueError('Explicit consent confirmation is required')
    with connect() as c:
        cur=c.execute('''INSERT INTO faculty_profiles(full_name,email,department,scholar_url,scopus_id,wos_id,consent_scholar,consent_scopus,consent_wos,consent_at,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(name,email,dept,str(d.get('scholar_url','')).strip(),str(d.get('scopus_id','')).strip(),str(d.get('wos_id','')).strip(),*map(int,flags),now() if any(flags) else '',now(),now()))
        pid=cur.lastrowid; audit(c,'FACULTY_PROFILE_CREATED',None,name,{'faculty_id':pid,'consent_sources':[s for s,v in zip(['Google Scholar','Scopus','Web of Science'],flags) if v]})
    return pid

def add_citation(d):
    ensure_tables(); fid=int(d.get('faculty_id') or 0); title=str(d.get('paper_title','')).strip(); source=str(d.get('source','')).strip(); url=str(d.get('source_url','')).strip()
    if not fid or not title or not source: raise ValueError('Faculty, paper title and source are required')
    citations=int(d.get('citations') or 0)
    if citations<0: raise ValueError('Citation count cannot be negative')
    if source not in ('Google Scholar','Scopus','Web of Science','Crossref','Manual verified entry'): raise ValueError('Select a supported source label')
    with connect() as c:
        if not c.execute('SELECT id FROM faculty_profiles WHERE id=?',(fid,)).fetchone(): raise ValueError('Faculty profile not found')
        cur=c.execute('''INSERT INTO citation_records(faculty_id,paper_title,doi,publication_year,citations,source,source_url,retrieved_at,verification_status)
          VALUES(?,?,?,?,?,?,?,?,?)''',(fid,title,str(d.get('doi','')).strip(),str(d.get('publication_year','')).strip(),citations,source,url,now(),'Pending Verification'))
        audit(c,'CITATION_RECORD_ADDED',None,str(fid),{'citation_id':cur.lastrowid,'source':source,'title':title})
        return cur.lastrowid

def run_workflow(fid):
    ensure_tables()
    with connect() as c:
        p=c.execute('SELECT * FROM faculty_profiles WHERE id=?',(fid,)).fetchone()
        if not p: raise ValueError('Faculty profile not found')
        output={'coordinator':'apniLeap AURA Coordinator','faculty_profile_agent':{'status':'completed','profile':dict(p)},'agents':{},'execution_mode':'Hybrid: independent source checks in parallel; deduplication, analytics and validation are gated sequentially','published':False}
        # Parallel-source stage is represented explicitly. No external call is claimed unless configured.
        cs=connector_status()
        for key,agent,consent in [('Google Scholar','Google Scholar Harvest Agent',p['consent_scholar']),('Scopus','Scopus/WoS Verification Agent',p['consent_scopus']),('Web of Science','Scopus/WoS Verification Agent',p['consent_wos'])]:
            ready=bool(consent and cs[key]['configured'])
            output['agents'][key]={'agent':agent,'status':'ready_for_connector' if ready else 'blocked_or_not_configured','detail':cs[key]['mode'],'consent':bool(consent),'records_harvested':0,'note':'No live retrieval was performed in this local build.'}
        rows=[dict(x) for x in c.execute('SELECT * FROM citation_records WHERE faculty_id=? ORDER BY id',(fid,))]
        verified=[x for x in rows if x['verification_status']=='Verified']
        duplicate_groups=[]
        for i,a in enumerate(rows):
            for b in rows[i+1:]:
                if (a.get('doi') and a['doi'].lower()==(b.get('doi') or '').lower()) or (a['paper_title'].strip().lower()==b['paper_title'].strip().lower()):
                    duplicate_groups.append({'records':[a['id'],b['id']],'title':a['paper_title'],'status':'Flagged — reviewer confirmation required'})
        output['agents']['Duplicate Detection Agent']={'status':'completed','candidate_duplicates':duplicate_groups,'records_reviewed':len(rows),'auto_merge':False}
        counts=sorted([int(x['citations']) for x in verified],reverse=True); h=sum(1 for i,v in enumerate(counts,1) if v>=i)
        output['agents']['Citation Analytics Agent']={'status':'completed_with_limited_data','verified_publication_count':len(verified),'verified_citation_total':sum(counts),'h_index':h,'year_trend':{},'method':'h-index computed from citation counts of records marked Verified only','unverified_records_excluded':len(rows)-len(verified)}
        for x in verified:
            y=x.get('publication_year') or 'Unspecified'; output['agents']['Citation Analytics Agent']['year_trend'][y]=output['agents']['Citation Analytics Agent']['year_trend'].get(y,0)+1
        missing=[]
        if not p['department']: missing.append('Department missing')
        if not any([p['consent_scholar'],p['consent_scopus'],p['consent_wos']]): missing.append('No external-source consent recorded')
        if any(not x['source_url'] for x in verified): missing.append('Verified citation record missing source URL')
        output['agents']['Validation Agent']={'status':'passed_with_warnings' if missing else 'passed','warnings':missing,'checks':['Faculty profile exists','Consent recorded per selected source','Verified citation records retain source provenance','Unresolved duplicate candidates flagged']}
        output['agents']['Dashboard Agent']={'status':'awaiting_research_office_approval','message':'Dashboard and NIRF/NAAC export remain unpublished until authorized Research Office approval.'}
        status='Awaiting Research Office Review'
        cur=c.execute('INSERT INTO workflow_runs(faculty_id,status,started_at,completed_at,output) VALUES(?,?,?,?,?)',(fid,status,now(),now(),json.dumps(output,ensure_ascii=False)))
        rid=cur.lastrowid; audit(c,'AGENT_WORKFLOW_COMPLETED',None,'apniLeap AURA Coordinator',{'run_id':rid,'faculty_id':fid,'status':status})
        return {'id':rid,'status':status,'output':output}

def approve_run(run_id,user):
    ensure_tables()
    with connect() as c:
        r=c.execute('SELECT * FROM workflow_runs WHERE id=?',(run_id,)).fetchone()
        if not r: raise ValueError('Workflow run not found')
        if user['role'] not in ('HOD','Dean','Research Office'): raise PermissionError('Research Office / HoD / Dean approval required')
        c.execute("UPDATE workflow_runs SET status='Approved',approved_by=?,approved_at=? WHERE id=?",(user['full_name']+' · '+user['role'],now(),run_id))
        out=json.loads(r['output']);out['published']=True;out['agents']['Dashboard Agent']['status']='approved_for_publication';out['agents']['Dashboard Agent']['approved_by']=user['full_name']
        c.execute('UPDATE workflow_runs SET output=? WHERE id=?',(json.dumps(out,ensure_ascii=False),run_id))
        audit(c,'INTELLIGENCE_APPROVED',None,user['full_name'],{'run_id':run_id,'faculty_id':r['faculty_id']})

def resolve_duplicate(primary_id, duplicate_id, user):
    ensure_tables()
    with connect() as c:
        if user['role'] not in ('HOD','Dean','Research Office'):
            raise PermissionError('Research Office / HoD / Dean access required')
        a=c.execute('SELECT * FROM citation_records WHERE id=?',(primary_id,)).fetchone()
        b=c.execute('SELECT * FROM citation_records WHERE id=?',(duplicate_id,)).fetchone()
        if not a or not b: raise ValueError('Both citation records must exist')
        if a['id']==b['id'] or a['faculty_id']!=b['faculty_id']: raise ValueError('Select two different records belonging to the same faculty profile')
        same_doi=bool(a['doi'] and b['doi'] and a['doi'].lower()==b['doi'].lower())
        same_title=a['paper_title'].strip().lower()==b['paper_title'].strip().lower()
        if not (same_doi or same_title): raise ValueError('The records do not meet the duplicate matching rule')
        c.execute("UPDATE citation_records SET merged_into=?,verification_status=? WHERE id=?",(primary_id,'Merged · Linked to #'+str(primary_id),duplicate_id))
        audit(c,'DUPLICATE_MERGED',None,user['full_name'],{'primary_citation_id':primary_id,'duplicate_citation_id':duplicate_id,'preserved_original':True})

def report_csv():
    ensure_tables()
    with connect() as c:
        approved=c.execute("SELECT * FROM workflow_runs WHERE status='Approved' ORDER BY id DESC").fetchall()
        rows=[]
        for r in approved:
            out=json.loads(r['output']); a=out['agents']['Citation Analytics Agent']; p=c.execute('SELECT full_name,department FROM faculty_profiles WHERE id=?',(r['faculty_id'],)).fetchone()
            evidence=c.execute("SELECT source,source_url FROM citation_records WHERE faculty_id=? AND verification_status='Verified' ORDER BY id",(r['faculty_id'],)).fetchall()
            sources='; '.join(sorted(set(x['source'] for x in evidence)))
            source_urls='; '.join(x['source_url'] for x in evidence if x['source_url'])
            rows.append({'faculty':p['full_name'],'department':p['department'],'verified_publications':a['verified_publication_count'],'verified_citations':a['verified_citation_total'],'h_index':a['h_index'],'source_names':sources,'source_record_urls':source_urls,'approved_by':r['approved_by'],'approved_at':r['approved_at'],'workflow_run':r['id']})
    return rows
