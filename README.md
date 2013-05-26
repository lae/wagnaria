# README

Wagnaria is a WSGI application built on the [Bottle][] python web framework, 
using MongoDB (and pymongo) as its datastore backend.

### Requirements
- The [pymongo library][], and of course, MongoDB.

Wagnaria uses wsgiref by default, but you may want to substitute a different  
server for production. It's been developed with [gunicorn][] in mind, behind a 
nginx proxy.

### Configuration
Copy `config.yaml.example` to `config.yaml`, and modify keys as needed.

Any keys added to `bottle_run` will be dynamically read by the application, so 
you can also specify additional parameters for [`bottle.run()`][] if you'd like 
(e.g. `server: cherrypy`).

The defaults (if you don't copy the example over) are to start the application 
on localhost, port 9002, in debug mode. The application also connects to the 
`wagnaria` MongoDB on localhost:27017. By default, it also reloads on file 
changes (not recommended for production). For more information, see 
[`bottle.run()`][].

### Starting the application
Standalone, which I use for debugging:

	$PATH_TO/wagnaria.py

As for Gunicorn, I use a socket and 4 workers:

	gunicorn wagnaria:app --bind unix:/tmp/gunicorn-wagnaria.sock -w 4

And bind it to nginx, using SSL:

	upstream wagnaria {
		server unix:/tmp/gunicorn-wagnaria.sock fail_timeout=0;
	}
	# This redirects HTTP traffic to HTTPS
	server {
		server_name     $name;
		listen          $name:80;
		rewrite         ^ https://$server_name$request_uri? permanent;
	}
	server {
		server_name             $name;
		listen                  $ip:443 ssl;
		ssl_certificate         /etc/ssl/http/$name.pem;
		ssl_certificate_key     /etc/ssl/http/$name.key;
		access_log              logs/access_logs/$name;
		keepalive_timeout       70;
		location / {
			try_files $uri @wagnaria;
		}
		location @wagnaria {
			proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
			proxy_set_header        Host $host;
			proxy_redirect          off;
			proxy_pass              http://wagnaria;
		}
	}

[Bottle]: http://bottlepy.org
[pymongo library]: http://api.mongodb.org/python/current/
[gunicorn]: http://gunicorn.org
[`bottle.run()`]: http://bottlepy.org/docs/dev/api.html#bottle.run
