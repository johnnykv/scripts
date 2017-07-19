import sqlite3
import csv
import glob
import elasticsearch
from elasticsearch import helpers

from datetime import datetime

import geoip2.database
import geoip2.errors


ES_INDEX = 'heralding-activity'
DOC_TYPE = 'heralding-activty-type'

def fetchHeraldingEntry():
    conn = sqlite3.connect('heralding_analyze.db')
    conn.text_factory = str
    cursor = conn.cursor()

    query = 'SELECT * FROM auth'
    for row in cursor.execute(query):

        geoLocationCoordinates = None
        geoLocationCity = None
        geoLocationCountry = None

        try:
            geoResponse = geoReader.city(row[3])
            if 'en' in geoResponse.city.names:
                geoLocationCity = geoResponse.city.names['en']
            if 'en' in geoResponse.country.names:
                geoLocationCountry = geoResponse.country.names['en']
            if geoResponse.location is not None and geoResponse.location.longitude is not None:
                geoLocationCoordinates = '{0},{1}'.format(geoResponse.location.latitude, geoResponse.location.longitude)
        except geoip2.errors.AddressNotFoundError:
            pass
        try:
            username = str(row[8]).encode('ascii')
            password = str(row[9]).encode('ascii')
        except UnicodeDecodeError:
            # TODO: Log how often this happens
            print 'unicode error'
            continue

        entry = {
                    '_index': ES_INDEX,
                    '_type': DOC_TYPE,
                    '_id': row[1],
                    '_source': {
                        'timestamp': datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f' if '.' in row[0] else '%Y-%m-%d %H:%M:%S'),
                        'auth_id': row[1],
                        'session_id': row[2],
                        'source_ip': row[3],
                        'source_port': row[4],
                        'destination_ip': row[5] if row[5] != '' else None,
                        'destination_port': row[6],
                        'protocol': row[7],
                        'username': username,
                        'username_r': username,
                        'password': password,
                        'password_r': password,
                        'source_city': geoLocationCity,
                        'source_country': geoLocationCountry,
                        'source_location': geoLocationCoordinates
                    }
                }
        yield entry
    conn.close()

if __name__ == '__main__':
    geoReader = geoip2.database.Reader('GeoIP2-City.mmdb')

    es = elasticsearch.Elasticsearch('192.168.88.205')

    # es mapping
    heralding_mapping = {
        'timestamp': {
            'type': 'date',
            },
        'source_ip': {
            'type': 'string',
            'index': 'not_analyzed',
            'fields': {
                'ipv4': {
                    'type': 'ip',
                    }
                }
            },
        'destination_ip': {
            'type': 'string',
            'index': 'not_analyzed',
            'fields': {
                'ipv4': {
                'type': 'ip',
                    }
                }
            },
        'source_location': {
            'type': 'geo_point'
            },
        'source_port' : {
            'type': 'integer'
            },
        'destination_port' : {
            'type': 'integer'
                },
        'username_r' : {
            'type': 'string',
            'index': 'not_analyzed'
                },
        'password_r' : {
            'type': 'string',
            'index': 'not_analyzed'
                }
        }

    if es.indices.exists(ES_INDEX):
        print '[*] Deleting index'
        es.indices.delete(ES_INDEX)
    es.indices.create(ES_INDEX)
    es.indices.put_mapping(index=ES_INDEX, doc_type=DOC_TYPE, body={'properties': heralding_mapping})
    print '[*] Starting bulk insert'
    helpers.bulk(es, fetchHeraldingEntry(), chunk_size=10000, raise_on_exception=False)
