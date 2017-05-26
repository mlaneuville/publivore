'''
TODO
'''

import argparse
import sys
from tools import *

if sys.version_info < (3, 5, 0):
    sys.stderr.write("You need python 3.5 or later to run this script\n")
    sys.exit(-1)

parser = argparse.ArgumentParser()
parser.add_argument('-k', '--keywords', action="append", help="Choose keyword to investigate")
parser.add_argument('-j', '--journal', help="Choose keyword to investigate")
parser.add_argument('-t', '--timestamp', help="Choose keyword to investigate")
args = parser.parse_args()

DATABASE = connect_db()

world = search_query(DATABASE, 'world', keywords=args.keywords,
                                        journal=args.journal, 
                                        timestamp=args.timestamp)

liked = []
lib = query_db(DATABASE, "select * from library", one=False)
for paper in lib:
    liked.append(paper[0])

for item in world:
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

