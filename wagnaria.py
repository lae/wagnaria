#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
from datetime import datetime as dt
import json
import re
import collections

from pymongo import MongoClient
from bson.json_util import dumps, loads
from bson.objectid import ObjectId

import bottle
from bottle import HTTPError, request, response

POSITIONS = ('translator', 'editor', 'timer', 'typesetter')

class Wagnaria(object):
    """ Main application that serves as a hypervisor to Bottle. """
    def __init__(self):
        # Default Settings. You can place overrides in config.yaml.
        # 'bottle_run' settings are only used when executed standalone.
        self.config = {
            'mongo': {
                'host': 'localhost',
                'name': 'wagnaria',
                'port': 27017
            },
            'bottle_run': {
                'host': 'localhost',
                'debug': True,
                'port': 9002
            }
        }
        # Overwrite settings if a config file exists.
        try:
            cfg = open('config.yaml')
        except IOError as e:
            print("I/O Error %s, %s (%s)" % (e.errno, e.strerror, e.filename),
                "\nContinuing with default configuration.")
            cfg = ''
        if cfg:
            try:
                self.config.update(yaml.load(cfg))
            except Exception:
                print(e + "\nQuitting because I could not properly interpret",
                      "config.yaml; check that your syntax is correct.")
                exit(1)
            finally:
                cfg.close()

        # Establish a MongoDB connection.
        try:
            self.client = MongoClient(self.config['mongo']['host'],
                                      self.config['mongo']['port'])
        except Exception:
            print(e + "\nUnable to connect to MongoDB, quitting.")
            exit(1)
        # Load the database if it exists, create it if it doesn't.
        self.db = self.client[self.config['mongo']['name']]

        # Assign this object to the first app in Bottle's AppStack().
        self.app = bottle.Bottle()
        # Setup the routes to be handled by this object.
        self.install_routes(self.app)

        self.api = WagnariaAPI(self.db)
        self.app.mount('/api/1/', self.api.app)

        if __name__ == '__main__':
            # Run app using bottle_run settings if executed standalone.
            sb = []
            for k, v in self.config['bottle_run'].items():
                if isinstance(v, str):
                    sb.append("%s='%s'" % (k, v))
                else:
                    sb.append("%s=%s" % (k, v))
            print("Started:", str(dt.now()))
            eval("self.app.run({0})".format(', '.join(sb)))

    def index(self):
        """ Return an index page. """
        return("<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you "
               "join me \nin the oak tree?</pre>")

    def simple(self):
        """ Return a JS-free table of shows. """
        airing = loads(self.api.shows.by_group('airing'))
        now = dt.utcnow()
        positions = [
            ['translator', 'translated'],
            ['editor', 'edited'],
            ['timer', 'timed'],
            ['typesetter', 'typeset']
        ]
        tbl_airing = []
        for show in sorted(airing, key=lambda k: k['airtime']):
            encoded = "Yes" if show['progress']['encoded'] else "No"
            eta = (show['airtime'] - loads(dumps(now))).total_seconds()/60
            row_class = {
                True: 'subbing',
                False: {
                    True: 'airing_1',
                    False: {
                        True: 'airing_3',
                        False: {
                            True: 'airing_6',
                            False: {
                                True: 'airing_12',
                                False: ''
                            }.get(eta<=720)
                        }.get(eta<=360)
                    }.get(eta<=180)
                }.get(eta<=60)
            }.get(eta<0)
            row = '<tr class="%s">' % row_class
            row += '<td class="title">%s</td>' % show['titles']['english']
            row += '<td>%d (of %d)</td>' % (show['episodes']['current'] + 1,
                                            show['episodes']['total'])
            row += '<td>%s</td>' % show['airtime']
            row += '<td><a href="%s"><i class="icon-black ' % show['link']
            row += 'icon-info-sign"></i></a></td>'
            for p in positions:
                row += '<td class="staff-status-%s">%s</td>' % (
                        str(show['progress'][p[1]]).lower(),
                        show['staff'][p[0]]['name']
                    )
            row += '<td class="staff-status-%s encoded-status">%s</td>' %\
                    (str(show['progress']['encoded']).lower(), encoded)
            tbl_airing.append(row)
        table = '<div id="食べ物" class="pure-u">' \
            '<table class="pure-table pure-table-horizontal"><thead><tr>' \
            '<th>Series</th><th>Episode</th><th>airs on</th><th>Archive</th>' \
            '<th>Translator</th><th>Editor</th><th>Timer</th>' \
            '<th>Typesetter</th><th>Encoded?</th></tr></thead>'\
            '<tbody>%s</tbody></table></div>' % ''.join(tbl_airing)
        body = '<!DOCTYPE html><html lang="en"><head>' \
            '<title>Wagnaria!</title>' \
            '<link href="css/pure-min.css" rel="stylesheet" media="screen">' \
            '<link href="css/glyphs.min.css" rel="stylesheet" media="screen">' \
            '<link href="css/main.css" rel="stylesheet" media="screen">' \
            '</head><body>%s</body></html>' % table
        response.content_type = "text/html"
        return body

    def install_routes(self, b):
        """ Define routes to their select functions for a Bottle app. """
        b.route('/', 'ANY', self.index)
        b.route('/simple', 'GET', self.simple)

class WagnariaAPI(object):
    """ API with JSON only responses """
    def __init__(self, mongodb):
        # Initialize class objects for shows and staff.
        self.db = mongodb
        self.staff = StaffCollection(self.db.staff, self.db.shows)
        self.shows = ShowsCollection(self.db.shows, self.db.staff)

        self.app = bottle.Bottle()
        # ObjectId Filter
        self.app.router.add_filter('oid', lambda x: (r'[0-9a-f]{24}', ObjectId, str))
        # Setup the routes to be handled by this object.
        self.install_routes(self.app)
        # Assign most common "error" routes to a custom error handler.
        errors = {sc: self.error_page for sc in range(400, 415)}
        errors[500] = self.error_page
        self.app.error_handler = errors

    def error_page(self, e):
        """ Return JSON documents when the application returns an HTTPError. """
        response.content_type = 'application/json'
        return dumps({'status_code': e._status_code, 'message': e.body})

    def search(self):
        """ Return shows and staff whose names match query. """
        response.content_type = 'application/json'
        query = request.query.q
        rq = re.compile(query, re.IGNORECASE)
        documents = [{
                '_id': d['_id'],
                'type': 'show',
                'label': d['titles']['english'],
                'minor': d['titles']['japanese']
            } for d in self.shows.collection.find({'$or': [
                {'titles.english': rq},
                {'titles.japanese': rq},
                {'titles.short': rq}
            ]}, {'titles.english': 1, 'titles.japanese': 1})]
        documents = documents + [{
                '_id': d['_id'],
                'type': 'staff',
                'label': d['name']
            } for d in self.staff.collection.find({'name': rq})]
        if documents:
            return dumps(documents)
        else:
            raise HTTPError(404, 'No shows/staff matched. Query: %s' % query)

    def install_routes(self, b):
        """ Define routes to their select functions for a Bottle app. """
        b.route('/shows.json', 'GET', self.shows.all_docs)
        b.route('/shows/ref.json', 'GET', self.shows.all_docs_short)
        b.route('/shows/<oid:oid>.json', 'GET', self.shows.by_id)
        b.route('/shows/<oid:oid>/blame.json', 'GET', self.shows.impute)
        b.route('/shows/status.json', 'GET', self.shows.status_count)
        b.route('/shows/<oid:oid>/<key:re:[a-z_.]+>.json', 'GET', self.shows.by_id)
        b.route('/shows/<group:re:[a-z_]+>.json', 'GET', self.shows.by_group)
#        b.route('/shows/<oid:oid>.json', 'DELETE', self.shows.destroy)

        b.route('/staff.json', 'GET', self.staff.all_docs)
        b.route('/staff/ref.json', 'GET', self.staff.all_docs_short)
        b.route('/staff/<oid:oid>.json', 'GET', self.staff.by_id)
        b.route('/staff/<oid:oid>/shows.json', 'GET', self.staff.show_history)
#        b.route('/staff/<oid:oid>.json', 'DELETE', self.staff.destroy)

        b.route('/search.json', 'GET', self.search)

class RESTfulCollection(object):
    """ Defines common web functions for use with MongoDB collections """
    def __init__(self, collection):
        self.collection = collection

    def reply(self, data):
        """ Prepare a BSON dict to output as JSON in an HTTP response. """
        response.content_type = 'application/json'
        return dumps(data)

    def find_by_id(self, oid, projection=None):
        """ Locate a document by ObjectId oid. """
        document = self.collection.find_one(oid, projection)
        if document:
            return document
        else:
            raise HTTPError(404, 'Could not find document %s.' % str(oid))

    def find(self, query=None, projection=None):
        """ Locate documents, using a query if applicable. """
        documents = [d for d in self.collection.find(query, projection)]
        if documents:
            return documents
        else:
            raise HTTPError(404, 'No documents matched. Query: %s' %
                            str.replace(dumps(query), '\"', "'"))

    def all_docs(self):
        """ Return all documents in the collection. """
        return self.reply(self.find())

    def by_id(self, oid):
        """ Return a single document in the collection. """
        return self.reply(self.find_by_id(oid))

    def destroy(self, oid):
        """ Remove a document in the collection. """
        result = self.collection.remove(oid, safe=True)
        if result['n'] == 1:
            return self.reply({'status_code': 200, '_id': oid,
                               'message': 'Document successfully deleted.'})
        else:
            raise HTTPError(404, 'Could not find document %s.' % str(oid))

class ShowsCollection(RESTfulCollection):
    """ Extends RESTfulCollection for the shows collection """
    def __init__(self, shows_collection, staff_collection):
        self.collection = shows_collection
        self.staff = staff_collection

    def resolve_staff(self, show):
        """ Cross-reference a show to update it with staff member names. """
        for position in POSITIONS:
            member = show['staff'][position]
            if 'name' not in member:
                member['name'] = self.staff.find_one(member['id'])['name']
        return show

    def by_id(self, oid, key=None):
        """ Return a show, or a show's key. """
        show = self.resolve_staff(self.find_by_id(oid))
        if key:
            for k in key.split('.'):
                if k in show:
                    show = show[k]
                else:
                    show = False
            if show:
                show = {'_id': oid, key: show}
            else:
                raise HTTPError(404, "%s is undefined for this show." % key)
        return self.reply(show)

    def all_docs(self):
        """ Return a list of all shows. """
        shows = self.find()
        shows = map(lambda s: self.resolve_staff(s), shows)
        return self.reply(shows)

    def all_docs_short(self):
        """ Return a short list of shows with referential keys. """
        shows = self.find(None, {'titles': 1})
        return self.reply(shows)

    def by_group(self, group):
        """ Return a specific list of shows with pre-defined filters. """
        query = {
            'completed': {"status": "complete"},
            'incomplete': {"status": "incomplete"},
            'airing': { "status": "airing" },
            'unaired': { "status": "unaired" },
            'dropped': {"status": "dropped"},
            'aired': {"status": "airing", "progress.encoded": False,
                "airtime": {"$lt": dt.utcnow()}},
            'current_episodes': {"status": "airing",
                "episodes": {"current": {"$gt": 0}}}
        }.get(group)
        if not query:
            raise HTTPError(404, 'Group "{0}" does not exist.'.format(group))
        shows = self.find(query)
        shows = map(lambda s: self.resolve_staff(s), shows)
        return self.reply(shows)

    def status_count(self):
        """ Return counts for each status. """
        shows = [s['status'] for s in self.find()]
        counts = dict(collections.Counter(shows))
        return self.reply(counts)

    def impute(self, oid):
        """ Return information about who's stalling a show. """
        show = self.resolve_staff(self.find_by_id(oid))
        p = show['progress']
        at = {'_id': oid}
        if show['status'] == 'complete':
            at['position'] = 'complete'
        elif show['airtime'] > dt.utcnow():
            at['position'] = 'broadcaster'
            at['name'] = show['channel']
        elif not p['translated']:
            at['position'] = 'translator'
        elif not p['encoded']:
            at['position'] = 'encoding'
        elif not p['edited']:
            at['position'] = 'editor'
        elif not p['timed']:
            at['position'] = 'timer'
        elif not p['typeset']:
            at['position'] = 'typesetter'
        elif not p['qc']:
            at['position'] = 'qc'
        if at['position'] in POSITIONS:
            at['name'] = show['staff'][at['position']]['name']
            if 'id' in show['staff'][at['position']]:
                at['staff_id'] = show['staff'][at['position']]['id']
        at['episode'] = show['episodes']['current']
        return self.reply(at)

class StaffCollection(RESTfulCollection):
    """ Extends RESTfulCollection for the staff collection. """
    def __init__(self, staff_collection, shows_collection):
        self.collection = staff_collection
        self.shows = shows_collection

    def all_docs_short(self):
        """ Return a short list of staff with referential keys. """
        staff = self.find(None, {'name': 1})
        return self.reply(staff)

    def show_history(self, oid):
        """ Return a list of shows a staff member has worked on. """
        query = [{'staff.%s.id' % p: oid} for p in POSITIONS]
        results = self.shows.find({'$or': query})
        shows = map(lambda s: s['titles']['english'], results)
        return self.reply(shows)


wagnaria = Wagnaria()
app = wagnaria.app
