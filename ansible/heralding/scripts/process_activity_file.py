#!/usr/bin/env python
# Copyright (C) 2016 Johnny Vestergaard <jkv@unixcluster.dk>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Parses all Heralding CSV files in a directory and stores the data in a sqlite database.

import sqlite3
import csv
import glob
import os
import time
from argparse import ArgumentParser


def parse_csv_file(file_name):
    print 'Start parsing: {0}'.format(file_name)
    with open(file_name, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=',')
        row_count = 1
        header = next(csv_reader)

        try:
            for row in csv_reader:
                row_count += 1
                # old version of the csv file, need to inject destination_ip at the correct position
                if 'destination_ip' not in header:
                    row = row[0:5] + [''] + row[5:]
                yield row
        except Exception as ex:
            print "[!] Error in row: {0}".format(row_count + 1)
            raise ex

def get_number_of_rows(cursor):
    cursor.execute(
        "SELECT COUNT(*) from auth")
    return cursor.fetchone()[0]

def insert_many(cursor, to_insert):
    cursor.executemany("insert or ignore into auth VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", to_insert)

if __name__ == '__main__':
    parser = ArgumentParser(description='Heralding actvity file processing')

    group = parser.add_argument_group()
    parser.add_argument('-d', '--delete_source', action='store_true', default=False,
                        help='Deletes source CSV file after parsing.')
    parser.add_argument('path', help='Path to directory that contains heralding log files.')
    args = parser.parse_args()

    conn = sqlite3.connect('heralding.db')
    conn.isolation_level = None
    conn.text_factory = str
    cursor = conn.cursor()

    # Create table
    # timestamp,auth_id,session_id,source_ip,source_port,destination_ip,destination_port,protocol,username,password
    cursor.execute('PRAGMA journal_mode=WAL')
    cursor.execute('''CREATE TABLE IF NOT EXISTS auth
                 (timestamp text, auth_id text, session_id text, source_ip text, source_port text,
                 destination_ip text, destination_port text, protocol text, username text, password text)''')
    conn.commit()

    files_parsed = 0
    total_rows = 0
    for file_name in glob.glob("{0}/*.log".format(args.path)):
        print '[*] Starting file parsing: {0}'.format(file_name)
        start = time.time()
        cursor.execute('begin')
        files_parsed += 1
        rows = 0
        #rows_before_insert = get_number_of_rows(cursor)
        to_insert = []
        for row in parse_csv_file(file_name):
            for i in range(0,7):
                if row[i] is '':
                    # row 5 is destination_ip
                    if i is 5:
                        print 'Warning: Auth id {0} has no destination ip.'.format(row[1])
                    else:
                        print 'Error. Column {0} in {1} was empty. Total row: {2}'.format(i, file_name, row)
                        assert False
            to_insert.append(row)
            rows += 1
            if rows % 5000 == 0:
                insert_many(cursor, to_insert)
                to_insert = []
        # any leftovers?
        if len(to_insert) > 0:
            insert_many(cursor, to_insert)
        conn.commit()

        #rows_added = get_number_of_rows(cursor) - rows_before_insert
        total_rows += rows

        entries_per_second = 0
        if rows > 0:
            entries_per_second = rows / (time.time() - start)
        end = time.time()

        os.remove(file_name)
        print '[+] {0}: Had {1}. Entries per second: {2}'.format(file_name, rows, entries_per_second)

    print '[*] {0} files parsed. A total of {1} rows was added..'.format(files_parsed,
           total_rows)
    conn.close()
