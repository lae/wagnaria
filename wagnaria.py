#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, request, response, run
from bson.objectid import ObjectId
import json
import pymongo
import yaml

f = open('config.yaml')
settings = yaml.load(f)
f.close()

app = Bottle()

client = pymongo.MongoClient(settings['mongo']['host'], settings['mongo']['port'])
db = client[settings['mongo']['name']]

@app.route('/')
def index():
    return "<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you join me \nin the oak tree?</pre>"

@app.get('/shows')
def get_shows():
    shows = []
    for show in db.shows.find():
        show['_id'] = str(show['_id'])
        shows.append(show)
    return prepare_json(shows)

# maybe this route turned out to be a bad idea.
@app.get('/shows/<column:re:[a-z_{}]+>/<value>')
def get_shows(column, value):
    shows = []
    if value == "true":
        value = True
    for show in db.shows.find({column: value}):
        show['_id'] = str(show['_id'])
        shows.append(show)
    return prepare_json(shows)

@app.get('/shows/<group:re:[a-z_]+>')
def get_shows(group):
    query = {
        'complete': { "status": "complete" },
        'incomplete': { "status": { "$in": [ "airing", "incomplete" ] } },
        #'aired': { status: "airing", is_encoded: False, airtime: SOME_MATH_HERE }
        'current_episodes': { "status": "airing", "episodes": { "current": { "$gt": 0 } } }
        }.get(group)
    # aired: shows.find({status: 0, encoded: 0, airtime: {'$lt': "new DateTime"}})
    shows = []
    for show in db.shows.find(query):
        show['_id'] = str(show['_id'])
        shows.append(show)
    return prepare_json(shows)

@app.post('/shows/create')
def create_show():
    show_data = request.json
    #sanitization
    # shows.save(show_data)
    return show_data

@app.get('/show/<_id>')
def get_show(_id):
    show = db.shows.find_one({'_id': ObjectId(_id)})
    show['_id'] = str(show['_id'])
    return show

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
    # staff.find()
    return "List all staff."

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
    return json.dumps(ingredients)

run(app, host='0.0.0.0', port=8080, debug=True, reloader=True)
