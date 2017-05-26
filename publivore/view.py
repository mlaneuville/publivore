'''
TODO
'''

import argparse
from sqlite3 import dbapi2 as sqlite3
import sys

if sys.version_info < (3, 5, 0):
    sys.stderr.write("You need python 3.5 or later to run this script\n")
    sys.exit(-1)

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--keywords', action="append", help="Choose keyword to investigate")
parser.add_argument('-j', '--journal', help="Choose keyword to investigate")
args = parser.parse_args()

def connect_db():
    '''TODO'''
    sqlite_db = sqlite3.connect("as.db")
    sqlite_db.row_factory = sqlite3.Row
    return sqlite_db

def query_db(_db, _query, _args=(), one=False):
    '''TODO'''
    cur = _db.execute(_query, _args)
    res = cur.fetchall()
    return (res[0] if res else None) if one else res

DATABASE = connect_db()

if args.journal:
    size = query_db(DATABASE, "select * from world where journal='%s'"%args.journal, one=False)
else:
    size = query_db(DATABASE, "select * from world", one=False)

liked = []
lib = query_db(DATABASE, "select * from library", one=False)
for paper in lib:
    liked.append(paper[0])

for item in size:
    if not args.keywords:
        print(tuple(item))
        continue
    filtered = True
    for kw in args.keywords:
        if kw in str(item[1]):
            filtered = False
        else:
            filtered = True
            break
    if not filtered and item[0] not in liked:
        print(tuple(item))
