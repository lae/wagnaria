#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, HTTPError, request, response
from bson.json_util import dumps
import json
import pymongo
import yaml

f = open('config.yaml')
settings = yaml.load(f)
f.close()

# Connect to MongoDB and load database
client = pymongo.MongoClient(settings['mongo']['host'], settings['mongo']['port'])
db = client[settings['mongo']['name']]

# Pre-define routes and their respective functions
def install_routes(app):
    app.route('/', ['ANY'], index)
    app.route('/shows', ['GET'], get_shows)
    app.route('/shows/<column:re:[a-z_.]+>/<value>', ['GET'], get_shows)
    app.route('/shows/<group:re:[a-z_]+>', ['GET'], get_shows)

# Index page
def index():
    return "<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you join me \nin the oak tree?</pre>"

def get_shows(group=None, column=None, value=None):
    if group:
        query = {
            'complete': { "status": "complete" },
            'incomplete': { "status": { "$in": [ "unaired", "airing", "incomplete" ] } },
            # aired: shows.find({status: 0, encoded: 0, airtime: {'$lt': "new DateTime"}})
            'aired': { "status": "airing", "progress.encode": False, "airtime": {"$lt": "new Date()"} },
            'current_episodes': { "status": "airing", "episodes": { "current": { "$gt": 0 } } }
        }.get(group)
        if not query:
            raise HTTPError(404, "No such group.")
        shows = db.shows.find(query)
    elif column:
        # maybe this route turned out to be a bad idea.
        shows = db.shows.find({column: value})
    else:
        shows = db.shows.find()
    return prepare_json(shows)

app = Bottle()

@app.post('/shows/create')
def create_show():
    show_data = request.json
    #sanitization
    # shows.save(show_data)
    return show_data

@app.get('/show/<_id>')
def get_show(_id):
    return prepare_json([db.shows.find_one({'_id': ObjectId(_id)})])

@app.put('/show/<_id>')
def update_show(_id):
    show_data = request.json
    #sanitization, set values for null data
    # show.update({id: id}, {'$set': {show_data}})
    return show_data

@app.delete('/show/<_id')
def delete_show(_id):
    #check if exists
    # shows.remove({id: id})
    return {'success': True}

@app.get('/show/<_id>/blame')
def who_to_blame_for(_id):
    #resolve id function here
    # shows.find({id: id})
    return "Return position and value for whoever is stalling show '{0}'.".format(_id)

@app.get('/show/<_id>/<column:re:[a-z_]+>')
def get_show(_id, column):
    #resolve id function here
    # shows.find({id: id})
    return "Return value in the '{0}' field for show '{1}'.".format(column, _id)

@app.get('/staff')
def get_staff():
    return prepare_json(db.staff.find())

@app.post('/staff/create')
def add_new_member():
    member_data = request.json
    #sanitization
    # staff.save(member_data)
    return member_data

@app.get('/staff/<_id>')
def get_member(_id):
    # staff.find({id: id})
    return "Return information for staff member ID '{0}'.".format(_id)

@app.put('/staff/<_id>')
def update_member(_id):
    member_data = request.json
    #sanitization, set values for null data
    # staff.update({id: id}, {'$set': {member_data}})
    return member_data

@app.delete('/staff/<_id>')
def delete_member(_id):
    # staff.remove({id: id})
    return {'success': True}

@app.get('/staff/<_id>/shows')
def shows_worked_on(_id):
    # shows.find({$or: [{translator: id}, {typesetter: id}, {timer: id}, {editor: id}]})
    return "List all shows '{0}' has worked on.".format(_id)
    
def prepare_json(ingredients):
    response.content_type = 'application/json'
    #for item in ingredients:
        #item['_id'] = str(item['_id'])
    return dumps(ingredients)

install_routes(app)
app.run(host=settings['bottle']['host'], port=settings['bottle']['port'],
        debug=settings['bottle']['debug'], reloader=settings['bottle']['reloader'])
