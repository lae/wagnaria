#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from bottle import Bottle, run

app = Bottle()

@app.route('/')
def index():
    return "<pre>Strawberries and cream, \nbiscuits and tea, \nwon't you join me \nby the silk sea?</pre>"

run(app, host='0.0.0.0', port=8080, debug=True, reloader=True)
