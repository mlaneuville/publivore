'''
TODO
'''

from sqlite3 import dbapi2 as sqlite3

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

def format_entry(entry):
    '''TODO'''
    res = []
    for col in entry:
        if isinstance(col, str) and len(col) > 100:
            col = col[:99] + '...'
        res.append(col)
    return tuple(res)

def search_query(db, table, keywords=None, journal=None, timestamp=None):
    '''TODO'''
    if keywords:
        for kw in keywords:
            kwsplit = kw.split(':')
            if kwsplit[0] == 'date':
                timestamp = kwsplit[1]
                keywords.remove(kw)

    query = "SELECT * FROM "+ table
    if journal:
        query += " WHERE journal='%s'" % journal
    if timestamp:
        if journal:
            query += " AND"
        else:
            query += " WHERE"
        query += " timestamp>='%s'" % timestamp

    ret = query_db(db, query)

    pop, out = [], []
    for idx, item in enumerate(ret):
        if keywords:
            for kw in keywords:
                if kw not in item[1]:
                    pop.append(idx)
                    break
        out.append(format_entry(item))

    for idx in pop[::-1]:
        out.pop(idx)

    return out
