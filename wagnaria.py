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
        self.shows = RESTfulCollection(self.db.shows)
        self.app = bottle.default_app()
        # ObjectId Filter
        self.app.router.add_filter('oid', lambda x: (r'[0-9a-f]{24}', ObjectId, str))
        self.install_routes(self.app)
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

    # Pre-define routes and their respective functions
    def install_routes(self, b):
        b.route('/', ['ANY'], self.index)
        b.route('/shows', ['GET'], self.shows.find)
        b.route('/shows/<oid:oid>', ['GET'], self.shows.find_by_id)
"""    app.route('/shows/<oid:oid>/<column:re:[a-z_.]+>', ['GET'],
              load_show)
    app.route('/shows/<group:re:[a-z_]+>', ['GET'],
              load_shows)
    app.route('/shows', ['POST'], create_show)
    app.route('/shows/<oid:oid>', ['PUT'], modify_show)
    app.route('/shows/<oid:oid>', ['DELETE'], destroy_show)
    app.route('/shows/<oid:oid>/blame', ['GET'], blame_show)
    app.route('/staff', ['GET'], load_staff)
    app.route('/staff/<oid:oid>', ['GET'], load_member)
    app.route('/staff/<oid:oid>/shows', ['GET'],
              load_members_shows)
    app.route('/staff', ['POST'], create_member)
    app.route('/staff/<oid:oid>', ['PUT'], modify_member)
    app.route('/staff/<oid:oid>', ['DELETE'], destroy_member)"""

class RESTfulCollection(object):
    def __init__(self, collection):
        self.collection = collection
    def reply(self, data):
        response.content_type = 'application/json'
        return dumps(data)
    def find_by_id(self, oid):
        document = self.collection.find_one({'_id': oid})
        if document:
            return self.reply([document])
        else:
            raise HTTPError(404, 'Could not find document %s.' % str(oid))
    def find(self, query=None, projection=None):
        response.content_type = 'application/json'
        return dumps([doc for doc in self.collection.find(query, projection)])
    def create(self, document):
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

# Return JSON documents when the application returns an HTTPError
@bottle.error(404)
def missing_page(error):
    response.content_type = 'application/json'
    return dumps([{'status_code': error._status_code, 'message': error.body}])

def resolve_staff(show):
    for position in ('translator', 'editor', 'timer', 'typesetter'):
        if 'name' not in show['staff'][position]:
            show['staff'][position]['name'] = db.staff.find_one(
                {'_id': ObjectId(show['staff'][position]['id'])}
            )['name']
    return show

# Return a list of shows
def load_shows(group=None):
    if group:
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
        shows = db.shows.find(query)
    else:
        shows = db.shows.find()
    shows = map(lambda s: resolve_staff(s), shows)
    return prepare_json(shows)

# Return a show
def load_show(oid, column=None):
    show = [db.shows.find_one({'_id': ObjectId(oid)})]
    if not show:
        raise HTTPError(404, 'There is no show with an ObjectId of %s.' % oid)
    if not column:
        show = map(lambda s: resolve_staff(s), show)
        return prepare_json(show)
    else:
        field = db.shows.find_one({'_id': ObjectId(oid)},
                                  {column: 1, '_id': 0})
        if not field:
            raise HTTPError(404, 'The "%s" field does not exist for %s' %
                            column, show['titles']['english'])
        return prepare_json([field])

# Return a member's information
def load_member(oid):
    member = db.staff.find_one({'_id': ObjectId(oid)})
    if not member:
        raise HTTPError(404, 'There is no staff with an ObjectId of %s.' % oid)
    return prepare_json([member])

# Return a list of all staff
def load_staff():
    staff = db.staff.find()
    return prepare_json(staff)

# Return a list of shows a staff member has worked on
def load_members_shows(oid):
    oid = ObjectId(oid)
    results = db.shows.find({'$or': [{'staff.{0}.id'.format(p): oid} for p in 
        ('translator', 'editor', 'timer', 'typesetter')]})
    shows = map(lambda s: s['titles']['english'], results)
    return prepare_json(shows)

# Insert a new show into the shows collection
def create_show():
    show_data = request.json
    #sanitization
    # shows.save(show_data)
    return show_data

# Update a show's metadata
def modify_show(oid):
    show_data = request.json
    #sanitization, set values for null data
    # show.update({id: id}, {'$set': {show_data}})
    return show_data

# Return information about who's stalling a show
def blame_show(oid):
    #resolve id function here
    # shows.find({id: id})
    return "Return whoever is stalling show '{0}'.".format(oid)

# Insert a new member into the staff collection
def create_member():
    member_data = request.json
    #sanitization
    # staff.save(member_data)
    return member_data

# Update a member's metadata
def modify_member(oid):
    member_data = request.json
    #sanitization, set values for null data
    # staff.update({id: id}, {'$set': {member_data}})
    return member_data

wagnaria = Wagnaria()
app = wagnaria.app
