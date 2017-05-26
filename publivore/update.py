import argparse
import sys
from datetime import date
from sqlite3 import dbapi2 as sqlite3 

if sys.version_info<(3,5,0):
  sys.stderr.write("You need python 3.5 or later to run this script\n")
  sys.exit(-1)

parser = argparse.ArgumentParser()
parser.add_argument('idx', nargs='*', type=int, help="Choose keyword to investigate")
args = parser.parse_args()

def connect_db():
    sqlite_db = sqlite3.connect("as.db")
    sqlite_db.row_factory = sqlite3.Row
    return sqlite_db

def query_db(db, query, args=(), one=False):
    cur = db.execute(query, args)
    res = cur.fetchall()
    return (res[0] if res else None) if one else res

db = connect_db()

for idx in args.idx:
    size = query_db(db, "select * from library where paper_id=?", (idx,), one=False)
    print(size)
    if not size:
        print(idx)
        q = '''INSERT INTO library VALUES (?,?,?)'''
        db.execute(q, (idx, 0, date.today().isoformat()))
    else:
        q = '''DELETE FROM library where paper_id=?'''
        db.execute(q, (idx,))

db.commit()
