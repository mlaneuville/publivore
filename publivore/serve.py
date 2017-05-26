import sqlite3

from datetime import date
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from sklearn import svm
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
app = Flask(__name__)

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

@app.route("/analysis")
def analysis():
    size = query_db(DATABASE, "select * from world order by paper_id", one=False)
    corpus = []
    for item in size:
        corpus.append(item[1])
    
    size = query_db(DATABASE, "select * from library", one=False)
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
    sortix = sortix[int(sum(y)):int(sum(y))+5]

    data = []
    for idx in sortix:
        article = query_db(DATABASE, "select * from world where paper_id=%d"% (idx+1), one=False)[0]
        data.append(tuple(article))
    return render_template("analysis.html", data=data)

@app.route("/")
def main():
    return redirect(url_for('show_all'))

@app.route("/search", methods=['GET'])
def search():
    keyword = request.args.get('q', '')

    world = query_db(DATABASE, "select * from world", one=False)
    arr = []
    for item in world:
        filtered = True
        if keyword in item[1]:
            filtered = False
        if not filtered:
            arr.append(item)
    return render_template("show_entries.html", entries=arr)

@app.route("/show_liked")
def show_liked():
    world = query_db(DATABASE, "select * from world", one=False)
    likes = query_db(DATABASE, "select * from library", one=False)
    arr_likes = [world[x[0]-1] for x in likes]
    return render_template("show_entries.html", entries=arr_likes)

@app.route("/add_likes")
def add_likes():
    idx = request.args.get('idx', type=int)
    like = query_db(DATABASE, "select * from library where paper_id=%d"%idx, one=True)
    if like:
        q = '''DELETE FROM library where paper_id=?'''
        DATABASE.execute(q, (idx,))
    else:
        q = '''INSERT INTO library VALUES (?,?,?)'''
        DATABASE.execute(q, (idx, 0, date.today().isoformat()))
    DATABASE.commit()
    return redirect(url_for('show_all'))

@app.route("/show_all", methods=['POST', 'GET'])
def show_all():
    keyword = []
    if request.method == 'POST':
        keyword = request.form['keyword']

    world = query_db(DATABASE, "select * from world", one=False)
    arr = []
    for item in world:
        like = query_db(DATABASE, "select * from library where paper_id=%d"%item[0], one=True)
        if like:
            continue
        if keyword:
            filtered = True
            if keyword in item[1]:
                filtered = False
            if not filtered:
                arr.append(item)
        else:
            arr.append(item)
    return render_template("show_entries.html", entries=arr)
    
@app.route("/")
def hello():
    render_template("layout.html")
    return render_template("menu.html")

if __name__ == "__main__":
    app.run()
