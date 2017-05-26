'''
TODO
'''

import configparser
from sqlite3 import dbapi2 as sqlite3
import sys
import urllib

import feedparser
from rdflib import Graph, Namespace, URIRef

if sys.version_info < (3, 5, 0):
    sys.stderr.write("You need python 3.5 or later to run this script\n")
    sys.exit(-1)

def connect_db():
    '''TODO'''
    sqlite_db = sqlite3.connect("as.db")
    sqlite_db.row_factory = sqlite3.Row
    return sqlite_db

def query_db(_db, _query, args=(), one=False):
    '''TODO'''
    cur = _db.execute(_query, args)
    res = cur.fetchall()
    return (res[0] if res else None) if one else res

DATABASE = connect_db()

CONFIG = configparser.RawConfigParser()
CONFIG.read("publivore/main.cfg")

RSS = Namespace('http://purl.org/rss/1.0/')
DC = Namespace('http://purl.org/dc/elements/1.1/')
PRISM = Namespace('http://prismstandard.org/namespaces/1.2/basic/')

NUM = query_db(DATABASE, "select * from world")
print("Opening DB with %d entries" % len(NUM))

JOURNALS = CONFIG.items("journals-wiley")
for abbr, url in JOURNALS:
    print(abbr, url)

    g = Graph()
    g.load(URIRef(url))

    volume = g.value(URIRef(url), PRISM.volume)
    number = g.value(URIRef(url), PRISM.number)
    articles = g.triples((None, DC.title, None))

    counter = 0
    for article in articles:
        title = article[2].lower()

        exist = query_db(DATABASE, "select * from world where title=?", (title,), one=True)
        if not exist:
            q = '''INSERT INTO world (title, journal, volume, issue) VALUES (?,?,?,?)'''
            DATABASE.execute(q, (title, abbr, volume, number))
            DATABASE.commit()
            counter += 1

    print("Entries from %s added: %d" % (abbr, counter))

JOURNALS = CONFIG.items("journals-rss")
for abbr, url in JOURNALS:
    print(abbr, url)

    d = feedparser.parse(url)

    counter = 0
    for article in d.entries:
        if article.get("prism_section", -1) == -1:
            summary = article.summary

            start = summary.find('Volume')
            end = summary[start:].find('</br>')
            source = summary[start:start+end].split(" ")

            if len(source) == 2:
                volume = source[1]
                issue = -1
            elif len(source) == 4:
                volume = source[1][:-1]
                issue = source[3]
            else:
                volume = -1
                issue = -1
        else:
            if article.prism_section != 'Article':
                continue
            volume = article.prism_volume
            issue = article.prism_number

        title = article.title.lower()
        exist = query_db(DATABASE, "select * from world where title=?", (title,), one=True)
        if not exist:
            q = '''INSERT INTO world (title, journal, volume, issue) VALUES (?,?,?,?)'''
            DATABASE.execute(q, (title, abbr, volume, issue))
            DATABASE.commit()
            counter += 1

    print("Entries from %s added: %d" % (abbr, counter))

JOURNALS = CONFIG.items("journals-arxiv")
BASE_URL = 'http://export.arxiv.org/api/query?' # base api query url

for abbr, url in JOURNALS:
    print(abbr, url)
    counter = 0

    query = 'search_query=%s&sortBy=lastUpdatedDate&start=%i&max_results=%i' % ('cat:'+url, 0, 30)
    with urllib.request.urlopen(BASE_URL+query) as url:
        response = url.read()
        parse = feedparser.parse(response)
        for e in parse.entries:
            title = e.title.lower()

            exist = query_db(DATABASE, "select * from world where title=?", (title,), one=True)
            if not exist:
                q = '''INSERT INTO world (title, journal, volume, issue) VALUES (?,?,?,?)'''
                DATABASE.execute(q, (title, abbr, -1, -1))
                DATABASE.commit()
                counter += 1

    print("Entries from %s added: %d" % (abbr, counter))
