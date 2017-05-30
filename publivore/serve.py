'''
TODO
'''

from datetime import date
import random
import time

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn import svm
from flask import Flask, request, redirect, url_for, \
     render_template, flash, session, g
from werkzeug import check_password_hash, generate_password_hash

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
    if 'user_id' not in session.keys():
        flash("Please log in to see analysis.")
        return render_template("analysis.html")
        
    size = query_db(DATABASE, "select * from world order by paper_id", one=False)
    corpus = []
    for item in size:
        corpus.append(item[1])

    size = search_query(DATABASE, "library", user=session['user_id'])
    if len(size) < 5:
        flash("Please like at least 5 papers before trying the analysis.")
        return render_template("analysis.html")
        
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
    if 'user_id' not in session.keys():
        flash("Please log in to see analysis.")
        return redirect(url_for('show_all'))

    idx = request.args.get('idx', type=int)
    like = query_db(DATABASE, "select * from library where paper_id=%d"%idx, one=True)
    if like:
        q = '''DELETE FROM library where paper_id=?'''
        DATABASE.execute(q, (idx,))
    else:
        q = '''INSERT INTO library VALUES (?,?,?)'''
        DATABASE.execute(q, (idx, session['user_id'], date.today().isoformat()))
    DATABASE.commit()
    return redirect(url_for('show_all'))

@APP.route("/show_liked")
def show_liked():
    '''TODO'''
    world = search_query(DATABASE, 'world')
    userid = "-1"
    if 'user_id' in session.keys():
        userid = session['user_id'] 
    else:
        flash("Please log in to store likes.")
    likes = search_query(DATABASE, 'library', user=userid)
    arr_likes = [world[x[0]-1] for x in likes]
    arr_likes = sorted(arr_likes, key=lambda k: k[5], reverse=True)
    dates = []
    for row in arr_likes:
        if row[5] not in dates:
            dates.append(row[5])
    return render_template("show_entries.html", entries={'data':arr_likes, 'dates':dates})

@APP.route("/show_all")
def show_all():
    '''TODO'''
    world = search_query(DATABASE, 'world')
    world = sorted(world, key=lambda k:k[0], reverse=True)
    dates = []
    for row in world:
        if row[5] not in dates:
            dates.append(row[5])
    return render_template("show_entries.html", entries={'data':world, 'dates':dates})

def get_user_id(username):
  """Convenience method to look up the id for a username."""
  rv = query_db(DATABASE, 'select user_id from users where username = ?',
                [username], one=True)
  return rv[0] if rv else None

@APP.route("/login", methods=['POST'])
def login():
    if not request.form['username']:
        flash("You have to enter a username")
    elif not request.form['password']:
        flash("You have to enter your password")
    elif get_user_id(request.form['username']) is not None:
        user = query_db(DATABASE,'''select * from users where username = ?''', [request.form['username']], one=True)
        if check_password_hash(user['pw_hash'], request.form['password']):
            # password is correct, log in the user
            session['user_id'] = get_user_id(request.form['username'])
            session['username'] = request.form['username']
            flash('User ' + request.form['username'] + ' logged in.')
        else:
            # incorrect password
            flash('User ' + request.form['username'] + ' already exists, wrong password.')
    else:
        # create account and log in
        creation_time = int(time.time())
        print(type(request.form['username']), type(generate_password_hash(request.form['password'])), creation_time)
        DATABASE.execute("insert into users (username, pw_hash, creation_time) values (?,?,?)",
                     (request.form['username'], 
                      generate_password_hash(request.form['password']), 
                      creation_time))
        user_id = DATABASE.execute('select last_insert_rowid()').fetchall()[0][0]
        DATABASE.commit()

        session['user_id'] = user_id
        session['username'] = request.form['username']
        flash('New account %s created' % (request.form['username'], ))
  
    return redirect(url_for('show_all'))

@APP.route('/logout')
def logout():
  session.pop('user_id', None)
  session.pop('username', None)
  flash('You were logged out')
  return redirect(url_for('show_all'))

if __name__ == "__main__":
    APP.secret_key = 'super secret key'
    APP.run()
