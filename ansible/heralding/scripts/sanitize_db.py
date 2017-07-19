import sqlite3

if __name__ == '__main__':
    conn = sqlite3.connect('heralding_analyze_sanitized.db')
    conn.text_factory = str
    cursor = conn.cursor()
    cursor.execute('CREATE INDEX IF NOT EXISTS index_source_ip ON auth (source_ip);')
    conn.commit()

    id_count = 0
    ip_ident = {}
    for row in cursor.execute('SELECT DISTINCT(source_ip) FROM auth'):
        assert row[0] not in ip_ident
        ip_ident[row[0]] = 'source_ip_{0}'.format(id_count)
        id_count = id_count + 1
    print '[*] Sanitizing {0} IPs in db'.format(id_count)

    count = 0
    for ip in ip_ident:
        cursor.execute('UPDATE auth SET source_ip=? WHERE source_ip=?', (ip_ident[ip], ip))
        if count % 5000 == 0:
            print '[*] I am alive!'
        count = count + 1
    conn.commit()
