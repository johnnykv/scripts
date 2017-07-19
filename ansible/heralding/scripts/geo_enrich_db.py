import sqlite3
import geoip2
import geoip2.database
import geoip2.errors

if __name__ == '__main__':
    conn = sqlite3.connect('heralding_analyze_sanitized.db')
    conn.text_factory = str
    cursor = conn.cursor()

    geoReader = geoip2.database.Reader('GeoIP2-City.mmdb')

    ips = []
    for row in cursor.execute('SELECT DISTINCT(source_ip) FROM auth'):
        ips.append(row[0])
    print '[*] Geo enriching {0} IPs in db'.format(len(ips))
    cursor.execute('CREATE INDEX IF NOT EXISTS index_source_ip ON auth (source_ip);')

    print '[*] Finished creating index'
    count = 0;
    for ip in ips:
        geoLocationCoordinates = None
        geoLocationCountry = None

        try:
            geoResponse = geoReader.city(ip)
            if 'en' in geoResponse.country.names:
                geoLocationCountry = geoResponse.country.names['en']
            if geoResponse.location is not None and geoResponse.location.longitude is not None:
                geoLocationCoordinates = '{0},{1}'.format(geoResponse.location.latitude, geoResponse.location.longitude)
        except geoip2.errors.AddressNotFoundError:
            pass
        cursor.execute('UPDATE auth SET source_ip_country=?, source_ip_lat_long=? WHERE source_ip=?', (geoLocationCountry, geoLocationCoordinates, ip))
        if count % 1000 == 0:
            print '[*] I am alive!'
        count = count + 1
