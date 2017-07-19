import sqlite3
import csv
import glob
from datetime import datetime


if __name__ == '__main__':

    backup_db = sqlite3.connect('heralding.db')
    backup_db.text_factory = str
    backup_db_cursor = backup_db.cursor()

    fix_db = sqlite3.connect('heralding.db')
    fix_db.text_factory = str
    fix_db_cursor = fix_db.cursor()

    counter = 0
    query = 'SELECT timestamp, auth_id from auth'
    fix_db_cursor.execute("begin")
    for row in backup_db_cursor.execute(query):
        counter += 1
        if counter % 50000 == 0:
            print '{0}: count!'.format(datetime.now())
        fix_db_cursor.execute('UPDATE auth SET timestamp=? WHERE auth_id=?', (row[0], row[1]))
    fix_db_cursor.execute("commit")
    backup_db_cursor.close()
    fix_db_cursor.close()
