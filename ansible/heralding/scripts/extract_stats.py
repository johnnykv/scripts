import sqlite3
import csv
import glob
import pprint

def get_count(conn, query_string):
    cursor.execute(query_string)
    return cursor.fetchone()[0]

def get_general_stats(cursor):
    result = {}
    result['total_login'] = get_count(cursor, "SELECT COUNT(auth_id) from auth")
    result['unique_usernames'] = get_count(cursor, "SELECT COUNT(DISTINCT username) from auth")
    result['unique_passwords'] = get_count(cursor, "SELECT COUNT(DISTINCT password) from auth")
    return result

def protocols_percentage(cursor):
    result = {}
    query = 'SELECT protocol, COUNT(auth_id), COUNT(auth_id)*100.0/(SELECT COUNT(auth_id) FROM auth) FROM auth GROUP ' \
            'BY protocol ORDER BY COUNT(protocol) DESC'
    for row in cursor.execute(query):
        result[row[0]] = {'count': row[1], 'percentage': row[2]}
    return result

def get_top_grouped_by(cursor, column_name, limit):
    result = {}
    limit = str(limit)
    for row in cursor.execute('SELECT COUNT(?), ' + column_name + ' FROM auth GROUP BY ' + column_name + ' ORDER BY '
                              'COUNT(?) DESC limit ?', (column_name, column_name, limit)):
        result[row[1]] = row[0]
    return result

if __name__ == '__main__':
    conn = sqlite3.connect('heralding_analyze.db')
    conn.text_factory = str
    cursor = conn.cursor()

    general_stats = get_general_stats(cursor)
    top_usernames = get_top_grouped_by(cursor, 'username', 15)
    top_passwords = get_top_grouped_by(cursor, 'password', 15)
    protocols_percentage = protocols_percentage(cursor)

    pp = pprint.PrettyPrinter(indent=4)
    print "************************************* TOTALS *************************************"
    pp.pprint(general_stats)
    print "************************************* PROTOCOL DISTRIBUTION *************************************"
    pp.pprint(protocols_percentage)
    print "************************************* TOP 15 USERNAMES *************************************"
    pp.pprint(top_usernames)
    print "************************************* TOP 15 PASSWORDS *************************************"
    pp.pprint(top_passwords)
    conn.close()
