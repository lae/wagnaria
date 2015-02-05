# -*- coding: utf-8 -*-

#import os

MONGO_HOST = "10.99.0.13"
MONGO_DBNAME = "wagnariav2"

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET', 'PATCH', 'DELETE']

URL_PREFIX = 'api'
API_VERSION = 'v2'
XML = False
VERSIONING = False
CACHE_CONTROL = 'max-age=20,must-revalidate'
CACHE_EXPIRES = 60

# MongoDB schemas
shows = {
    'schema': {
        'title': {
            'type': 'dict',
            'schema': {
                'english': {
                    'type': 'string',
                    'required': True,
                    'empty': False,
                    'unique': True
                },
                'japanese': { 'type': 'string' }
            }
        },
        'status': {
            'type': 'string',
            'required': True,
            'allowed': [
                'upcoming',
                'airing',
                'incomplete',
                'complete',
                'dropped'
            ]
        },
        'episodes': {
            'type': 'dict',
            'schema': {
                'current': { 'type': 'integer', 'default': 1 },
                'total': { 'type': 'integer' }
            }
        },
        "ended_on": { 'type': 'datetime' },
        'channel': { 'type': 'string' },
        'notes': { 'type': 'string' },
        'staff': {
            'type': 'dict',
            'required': True,
            'schema': {
                position: {
                    'type': 'list',
                    'required': True,
                    'minlength': 1,
                    'schema': {
                        'type': 'dict',
                        'schema': {
                            'display_name': { 'type': 'string' },
                            'entity': {
                                'type': 'objectid',
                                'required': True,
                                'data_relation': {
                                    'resource': 'staff',
                                    'field': '_id'
                                },
                            }
                        }
                    }
                } for position in [
                    'translator',
                    'editor',
                    'timer',
                    'typesetter',
                    'qc'
                ]
            }
        }
    }
}
shows['schema']['staff']['schema']['qc']['required'] = False
shows['schema']['staff']['schema']['qc']['minlength'] = 0

staff = {
    'pagination': False,
    'schema': {
        'name': {
            'type': 'string',
            'required': True,
            'empty': False,
            'unique': True
        },
        'active': {
            'type': 'boolean',
            'default': True
        },
        'position': { 'type': 'string' },
        'twitter': { 'type': 'string' },
        'level': { 'type': 'number', 'default': 0 }
    }
}

DOMAIN = {
    'shows': shows,
    'staff': staff
}
