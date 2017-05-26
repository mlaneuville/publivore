'''
TODO
'''

from datetime import date
import random

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn import svm
from flask import Flask, request, redirect, url_for, \
     render_template, flash

from tools import *
from retrieve import *

APP = Flask(__name__)
DATABASE = connect_db()

@APP.route("/")
def main():
    '''TODO'''
    return redirect(url_for('show_all'))

@APP.route("/update")
def update():
    '''TODO'''
    today = search_query(DATABASE, 'world', timestamp=date.today().isoformat())

    if len(today) > 0:
        flash("Already updated today!")
    else:
        for a, b in fetch_rss():
            print(a, b)
        for a, b in fetch_arxiv():
            print(a, b)
        for a, b in fetch_wiley():
            print(a, b)
        flash("Update in progress!")

    return render_template('update.html')

@APP.route("/analysis")
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
    data = {}
    data['clusters'] = []

    #clustering
    model = KMeans(n_clusters=2, init='k-means++', max_iter=100, n_init=1)
    model.fit(X[likes])

    order_centroids = model.cluster_centers_.argsort()[:, ::-1]
    terms = v.get_feature_names()
    for i in range(2):
        data['clusters'].append([])
        for ind in order_centroids[i, :3]:
            data['clusters'][-1].append(terms[ind])

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
    randidx = random.sample(range(int(sum(y)), int(sum(y))+50), 5)
    sortix = sortix[randidx]

    data['recomm'] = []
    for idx in sortix:
        article = query_db(DATABASE, "select * from world where paper_id=%d"% (idx+1), one=False)[0]
        data['recomm'].append(format_entry(article))

    return render_template("analysis.html", data=data)

@APP.route("/search", methods=['GET'])
def search():
    '''TODO'''
    keywords = request.args.get('q', '')
    keywords = keywords.split(',')

    world = search_query(DATABASE, 'world', keywords=keywords)
    return render_template("show_entries.html", entries=world)

@APP.route("/add_likes")
def add_likes():
    '''TODO'''
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

@APP.route("/show_liked")
def show_liked():
    '''TODO'''
    world = search_query(DATABASE, 'world')
    likes = search_query(DATABASE, 'library')
    arr_likes = [world[x[0]-1] for x in likes]
    return render_template("show_entries.html",
                           entries=sorted(arr_likes, key=lambda k: k[5]))

@APP.route("/show_all")
def show_all():
    '''TODO'''
    world = search_query(DATABASE, 'world')
    return render_template("show_entries.html",
                           entries=sorted(world, key=lambda k: k[5]), reverse=False)

if __name__ == "__main__":
    APP.secret_key = 'super secret key'
    APP.run()
