#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import yaml
from datetime import datetime as dt
import json

from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId

import bottle
from bottle import HTTPError, request, response

POSITIONS = ('translator', 'editor', 'timer', 'typesetter')

class Wagnaria(object):
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
        # Update settings if a config file exists.
        try:
            cfg = open('config.yaml')
        except (FileNotFoundError, PermissionError) as e:
            print(e + "\nContinuing with default configuration.")
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
        self.staff = StaffCollection(self.db.staff, self.db.shows)
        self.shows = ShowsCollection(self.db.shows, self.db.staff)
        self.app = bottle.default_app()
        # ObjectId Filter
        self.app.router.add_filter('oid', lambda x: (r'[0-9a-f]{24}', ObjectId, str))
        self.install_routes(self.app)
        # Assign most common "error" routes to a custom error handler.
        errors = {sc: self.error_page for sc in range(400, 415)}
        errors[500] = self.error_page
        self.app.error_handler = errors
        # Run app using the default wsgiref
        if __name__ == '__main__':
            sb = []
            for k, v in self.config['bottle_run'].items():
                if isinstance(v, str):
                    sb.append("%s='%s'" % (k, v))
                else:
                    sb.append("%s=%s" % (k, v))
            eval("bottle.default_app().run({0})".format(', '.join(sb)))

    # Index page
    def index(self):
        return("<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you "
               "join me \nin the oak tree?</pre>")

    # Return JSON documents when the application returns an HTTPError
    def error_page(self, error):
        response.content_type = 'application/json'
        return dumps({'status_code': error._status_code, 'message': error.body})

    # Pre-define routes and their respective functions
    def install_routes(self, b):
        b.route('/', 'ANY', self.index)
        b.route('/shows', 'GET', self.shows.all_docs)
        b.route('/shows/ref', 'GET', self.shows.all_docs_short)
        b.route('/shows/<oid:oid>', 'GET', self.shows.by_id)
        b.route('/shows/<oid:oid>/blame', 'GET', self.shows.impute)
        b.route('/shows/<oid:oid>/<key:re:[a-z_.]+>', 'GET', self.shows.by_id)
        b.route('/shows/<group:re:[a-z_]+>', 'GET', self.shows.by_group)
        b.route('/staff', 'GET', self.staff.all_docs)
        b.route('/staff/ref', 'GET', self.staff.all_docs_short)
        b.route('/staff/<oid:oid>', 'GET', self.staff.by_id)
        b.route('/staff/<oid:oid>/shows', 'GET', self.staff.show_history)
"""    
    app.route('/shows', ['POST'], create_show)
    app.route('/shows/<oid:oid>', ['PUT'], modify_show)
    app.route('/shows/<oid:oid>', ['DELETE'], destroy_show)
    app.route('/staff', ['POST'], create_member)
    app.route('/staff/<oid:oid>', ['PUT'], modify_member)
    app.route('/staff/<oid:oid>', ['DELETE'], destroy_member)"""

class RESTfulCollection(object):
    def __init__(self, collection):
        self.collection = collection
    def reply(self, data):
        response.content_type = 'application/json'
        return dumps(data)
    def find_by_id(self, oid, projection=None):
        document = self.collection.find_one(oid, projection)
        if document:
            return document
        else:
            raise HTTPError(404, 'Could not find document %s.' % str(oid))
    def find(self, query=None, projection=None):
        documents = [d for d in self.collection.find(query, projection)]
        if documents:
            return documents
        else:
            raise HTTPError(404, 'No documents matched. Query: ' + vars(query))
    def all_docs(self):
        return self.reply(self.find())
    def by_id(self, oid):
        return self.reply(self.find_by_id(oid))
    def create(self, document):
        #show_data = request.json
        try:
            oid = self.insert(document)
        except Exception as e:
            return "Could not insert document. "+e
    #def modify(self, oid, 
    def destroy(self, oid):
        try:
            self.collection.find_one({'_id': oid})
        except:
            return "No"
        try:
            info = self.remove(oid, safe=True)
        except:
            return "Something went terribly wrong. "+e
        return info

class ShowsCollection(RESTfulCollection):
    def __init__(self, shows_collection, staff_collection):
        self.collection = shows_collection
        self.staff = staff_collection
    def resolve_staff(self, show):
        for position in POSITIONS:
            member = show['staff'][position]
            if 'name' not in member:
                member['name'] = self.staff.find_one(member['id'])['name']
        return show
    def by_id(self, oid, key=None):
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
        shows = self.find()
        shows = map(lambda s: self.resolve_staff(s), shows)
        return self.reply(shows)
    def all_docs_short(self):
        shows = self.find(None, {'titles': 1})
        return self.reply(shows)
    def by_group(self, group):
        query = {
            'complete': {"status": "complete"},
            'incomplete': 
                {"status": {"$in": ["unaired", "airing", "incomplete"]}},
            'airing': { "status": "airing" },
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
    def impute(self, oid):
        # Return information about who's stalling a show
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
        return self.reply(at)

class StaffCollection(RESTfulCollection):
    def __init__(self, staff_collection, shows_collection):
        self.collection = staff_collection
        self.shows = shows_collection
    def all_docs_short(self):
        staff = self.find(None, {'name': 1})
        return self.reply(staff)
    def show_history(self, oid):
        # Return a list of shows a staff member has worked on
        query = [{'staff.%s.id' % p: oid} for p in POSITIONS]
        results = self.shows.find({'$or': query})
        shows = map(lambda s: s['titles']['english'], results)
        return self.reply(shows)


wagnaria = Wagnaria()
app = wagnaria.app
