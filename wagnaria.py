#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, run

app = Bottle()

@app.route('/')
def index():
    return "<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you join me \nby the silk sea?</pre>"

@app.get('/shows')
def get_shows():
    return "List all shows."

@app.get('/shows/<column:re:[a-z_]+>/<value>')
def get_shows(column, value):
    return "List all shows whose '{0}' field is set to '{1}'.".format(column, value)

@app.get('/shows/<group:re:[a-z_]+>')
def get_shows(group):
    return "List all shows in custom group '{0}'.".format(group)

@app.post('/shows/create')
def create_show():
    show_data = request.json
    #sanitization
    #ORM data handling
    return show_data

@app.get('/show/<id>')
def get_show(id):
    #resolve id function here
    return "Return information for show '{0}'.".format(id)

@app.put('/staff/<id:int>')
def update_show(id):
    show_data = request.json
    #sanitization, set values for null data
    #ORM data handling
    return show_data

@app.delete('/sshow/<id:int>')
def delete_show(id):
    #check if exists, and delete through ORM
    return {'success': True}

@app.get('/show/<id>/blame')
def who_to_blame_for(id):
    #resolve id function here
    return "Return position and value for whoever is stalling show '{0}'.".format(id)

@app.get('/show/<id>/<column:re:[a-z_]+>')
def get_show(id, column):
    #resolve id function here
    return "Return value in the '{0}' field for show '{1}'.".format(column, id)

@app.get('/staff')
def get_staff():
    return "List all staff."

@app.post('/staff/create')
def add_new_member():
    member_data = request.json
    #sanitization
    #ORM data handling
    return member_data

@app.get('/staff/<id:int>')
def get_member(id):
    return "Return information for staff member ID '{0}'.".format(id)

@app.put('/staff/<id:int>')
def update_member(id):
    member_data = request.json
    #sanitization, set values for null data
    #ORM data handling
    return member_data

@app.delete('/staff/<id:int>')
def delete_member(id):
    #check if exists, and delete through ORM
    return {'success': True}

@app.get('/staff/<id:int>/shows')
def shows_worked_on(id):
    return "List all shows '{0}' has worked on.".format(id)

run(app, host='0.0.0.0', port=8080, debug=True, reloader=True)
