import argparse,getpass,secrets,sqlite3
import server
p=argparse.ArgumentParser(description='Create an authorized AURA reviewer account')
p.add_argument('--id',required=True);p.add_argument('--name',required=True);p.add_argument('--role',required=True,choices=['HOD','Dean','Research Office'])
a=p.parse_args();server.init()
pw=getpass.getpass('New reviewer password (minimum 12 characters): ')
if len(pw)<12:raise SystemExit('Password must contain at least 12 characters')
confirm=getpass.getpass('Confirm password: ')
if pw!=confirm:raise SystemExit('Passwords do not match')
salt=secrets.token_hex(16)
with server.connect() as c:
 c.execute('INSERT INTO reviewers VALUES(?,?,?,?,?)',(a.id.lower(),a.name,a.role,salt,server.hash_password(pw,salt)))
 server.audit(c,'REVIEWER_CREATED',None,a.id.lower(),{'role':a.role})
print('Reviewer account created:',a.id.lower())
