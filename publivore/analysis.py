import pickle
import numpy as np
import sys
import argparse
from sklearn import svm
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlite3 import dbapi2 as sqlite3 

if sys.version_info<(3,5,0):
  sys.stderr.write("You need python 3.5 or later to run this script\n")
  sys.exit(-1)

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--num', type=int, default=5, help="Choose keyword to investigate")
parser.add_argument('-k', '--clusters', type=int, default=2, help="Choose keyword to investigate")
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

size = query_db(db, "select * from world order by paper_id", one=False)
corpus = []
for item in size:
    corpus.append(item[1])

size = query_db(db, "select * from library", one=False)
likes = []
for item in size:
    likes.append(item[0]-1)

v = TfidfVectorizer(input='content', encoding='utf-8', decode_error='replace',
                    strip_accents='unicode', lowercase=True, analyzer='word',
                    stop_words='english', token_pattern=r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b',
                    ngram_range=(1, 2), max_features=10000, norm='l2', use_idf=True,
                    sublinear_tf=True, max_df=1.0, min_df=1)

v.fit(corpus)
X = v.transform(corpus)

#clustering
model = KMeans(n_clusters=args.clusters, init='k-means++', max_iter=100, n_init=1)
model.fit(X[likes])

print("Top terms per cluster:")
order_centroids = model.cluster_centers_.argsort()[:, ::-1]
terms = v.get_feature_names()
for i in range(args.clusters):
    print("Cluster %d:" % i, end='')
    for ind in order_centroids[i, :2]:
        print(' %s,' % terms[ind], end='')
    print("")
print("")

# full matrix
out = {}
out['X'] = X
out['y'] = likes

X = X.todense()
y = np.zeros(X.shape[0])
for like in likes:
    y[like] = 1

clf = svm.LinearSVC(class_weight='balanced', verbose=False, max_iter=10000, tol=1e-6, C=0.1)

try:
    clf.fit(X, y)
except ValueError:
    print("Add at least one paper to your library to get recommendations!")
    sys.exit()

s = clf.decision_function(X)

sortix = np.argsort(-s)
sortix = sortix[int(sum(y)):int(sum(y))+args.num]

for idx, like in enumerate(likes):
    print("[%d] You liked: %s" % (model.predict(X[like]), corpus[like]))

print("You may also like:")
for idx in sortix:
    article = query_db(db, "select * from world where paper_id=%d"% (idx+1), one=False)[0]
    print("\t- [%d][%s] %s [%d]" % (article[0],article[2], article[1], model.predict(X[idx])))
