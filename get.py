#!/usr/bin/env python

import json
import logging
from optparse import OptionParser
import os.path
import sys
import time

from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run
import requests


def simplerepr(obj):
    keys = sorted(key for key in obj.__dict__.keys() if not key.startswith('_'))
    attrs = ''.join(' %s=%r' % (key, obj.__dict__[key]) for key in keys)
    return '<%s%s>' % (obj.__class__.__name__, attrs)


class Item(object):

    def __init__(self, item_json):
        self.id = item_json['id']
        self.published = item_json['published']
        self.geocode = item_json['geocode']

    def insert(self, table_id, query):
        return 'INSERT INTO %s (query, id, published, geocode) VALUES (\'%s\', \'%s\', \'%s\', \'%s\')' % (table_id, query, self.id, self.published, self.geocode)

    __repr__ = simplerepr


def main(argv):
    option_parser = OptionParser()
    option_parser.add_option('-c', '--create-table', action='store_true')
    option_parser.add_option('-t', '--table-name', default='devfestzurich', metavar='TABLE')
    option_parser.add_option('--table-id', default='1O7qsDkkgaDbAArUKywHVwPxVqz4RA9P1xEAfrHU', metavar='TABLE-ID')
    option_parser.add_option('-q', '--query', metavar='QUERY')
    option_parser.add_option('-k', '--key', default='AIzaSyBfoMH8qNEQYBjLA9u0jLgs5V6o7KiAFbQ', metavar='KEY')
    option_parser.add_option('-l', '--limit', default=20, metavar='LIMIT', type=int)
    option_parser.add_option('-f', '--fields', default='items(geocode,id,published),nextPageToken', metavar='FIELDS')
    option_parser.add_option('--client-id', default='265903001164-lrjmvjnqjl2sfa13ogofm3hj2roakqkj.apps.googleusercontent.com')
    option_parser.add_option('--client-secret', default='DgdHp4OsayYhTx3kPhXTYt1W')
    option_parser.add_option('--scope', default='https://www.googleapis.com/auth/fusiontables')
    option_parser.add_option('--log-level', default=0, type=int)
    option_parser.add_option('--verbose', '-v', action='count', dest='log_level')
    options, args = option_parser.parse_args(argv[1:])

    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.WARN - 10 * options.log_level)

    logger = logging.getLogger(os.path.basename(argv[0]))

    flow = OAuth2WebServerFlow(options.client_id, options.client_secret, options.scope)
    storage = Storage('credentials.dat')
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = run(flow, storage)

    plus_session = requests.session()
    ft_session = requests.session(headers={'Authorization': 'OAuth ' + credentials.access_token})

    if options.create_table:
        data = {
            'description': 'DevFest Zurich',
            'isExportable': True,
            'name': options.table_name,
            'columns': [
                {'name': 'id', 'type': 'STRING'},
                {'name': 'published', 'type': 'DATETIME'},
                {'name': 'query', 'type': 'STRING'},
                {'name': 'geocode', 'type': 'LOCATION'},
            ],
        }
        while True:
            ft_response = ft_session.post('https://www.googleapis.com/fusiontables/v1/tables', data=json.dumps(data), headers={'Content-Type': 'application/json'})
            if ft_response.status_code == 200:
                break
            elif ft_response.status_code == 401:
                credentials = run(flow, storage)
            else:
                print repr(ft_response)
                print repr(ft_response.content)
                raise RuntimeError

        print repr(ft_response)
        print repr(ft_response.json)

    params = {
        'fields': options.fields,
        'key': options.key,
        'maxResults': 20,
        'query': options.query,
        }
    count = 0
    while options.limit and count < options.limit:
        plus_response = plus_session.get('https://www.googleapis.com/plus/v1/activities', params=params)
        logging.info('got %d items, %d with geocode' % (len(plus_response.json['items']), len([item for item in plus_response.json['items'] if 'geocode' in item])))
        items = [Item(item_json) for item_json in plus_response.json['items'] if 'geocode' in item_json]
        for item in items:
            while True:
                time.sleep(2)
                ft_response = ft_session.post('https://www.googleapis.com/fusiontables/v1/query', headers={'Content-Length': '0'}, params={'sql': item.insert(options.table_id, options.query)})
                #print repr(ft_response)
                #print repr(ft_response.content)
                if ft_response.status_code == 200:
                    break
                elif ft_response.status_code == 401:
                    credentials = run(flow, storage)
                else:
                    print repr(ft_response)
                    print repr(ft_response.content)
                    raise RuntimeError
            count += len(items)
        if 'nextPageToken' in plus_response.json:
            params['pageToken'] = plus_response.json['nextPageToken']
        else:
            break


if __name__ == '__main__':
    sys.exit(main(sys.argv))
