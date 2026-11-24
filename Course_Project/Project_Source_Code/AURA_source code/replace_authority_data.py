import json, os
import server

def refresh():
    server.init()
    seed_path=os.path.join(server.ROOT,'seed_records.json')
    with open(seed_path,encoding='utf-8') as f:
        seed=json.load(f)
    with server.connect() as c:
        # Remove only historical imported/unverified rows. Keep new submissions,
        # reviewer accounts, sessions, and the audit history.
        removed=c.execute("DELETE FROM papers WHERE status='Imported · Unverified'").rowcount
        for r in seed:
            d={**r,'status':'Imported · Unverified',
               'source':r.get('source') or 'Authority spreadsheet · 2024–2026',
               'submission_date':'','submitted_by':'Authority import'}
            values=[str(d.get(field,'') or '') for field in server.FIELDS]
            c.execute(
                'INSERT INTO papers('+','.join(server.FIELDS)+',created_at,updated_at) VALUES('+
                ','.join('?' for _ in range(len(server.FIELDS)+2))+')',
                values+[server.now(),server.now()]
            )
        counts={}
        for row in c.execute("SELECT source,COUNT(*) AS n FROM papers WHERE status='Imported · Unverified' GROUP BY source"):
            counts[row['source']]=row['n']
        server.audit(c,'AUTHORITY_DATA_REPLACED',None,'System',
                     {'removed_old_imported_records':removed,'added_new_records':len(seed),'by_source':counts})
    print('Authority data replacement complete.')
    print('Old imported records removed:',removed)
    print('New authority records imported:',len(seed))
    for source,count in counts.items():
        print(f'{source}: {count}')
    print('New submissions and reviewer accounts were preserved.')

if __name__=='__main__':
    refresh()
