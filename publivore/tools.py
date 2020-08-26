'''
TODO
'''

from sqlite3 import dbapi2 as sqlite3

def query_db(query, args=(), one=False):
    '''TODO'''
    with sqlite3.connect("as.db") as db:
        db.row_factory = sqlite3.Row
        cur = db.execute(query, args)
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

def search_query(table, keywords=None, journal=None, timestamp=None, user=None):
    '''TODO'''
    if keywords:
        for kw in keywords:
            kwsplit = kw.split(':')
            if kwsplit[0] == 'date':
                timestamp = kwsplit[1]
                keywords.remove(kw)

    query = "SELECT * FROM "+ table
    if user:
        query += " WHERE user_id='%s'" % user
    if journal:
        query += " WHERE journal='%s'" % journal
    if timestamp:
        if journal:
            query += " AND"
        else:
            query += " WHERE"
        query += " timestamp>='%s'" % timestamp

    ret = query_db(query)

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
