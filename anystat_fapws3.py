#! /usr/bin/env python
import re
import json
import httplib
import datetime
import ordereddict

import pymongo
from bson import json_util
import fapws._evwsgi as evwsgi
import fapws.base
from webob import Request, Response


class StatCacher(object):
    """
    A class to allow us to accumulate stats for various collections.  Stats 
    are only added when commit() is called.
    """
    def __init__(self):
        self.connect_to_mongo()

    def connect_to_mongo(self):
        self.connection = pymongo.Connection()
        self.db_cache = {}

    def add(self, db_name, collection_name, stat):
        collections = self.db_cache.setdefault(db_name, {collection_name:[]})
        collection = collections.setdefault(collection_name, [])
        collection.append(stat)

    def get(self, db_name, collection_name, *args, **kwargs):
        on_disk = self.connection[db_name][collection_name].find(*args, **kwargs)
        in_mem = self.db_cache.get(db_name, {}).get(collection_name,[])
        return list(on_disk) + in_mem

    def commit(self):
        for db_name, collections in self.db_cache.iteritems():
            for collection_name, stats in collections.iteritems():
                ids = self.connection[db_name][collection_name].insert(stats)
                if len(ids) < len(stats):
                    raise Exception("Failed to sync all stats to the database (tried %d, saved %d)."%(len(ids), len(stats)))
                self.db_cache[db_name][collection_name] = []


    def __getitem__(self, name):
        return self.db_cache[name]

class RequestDispatcher(object):
    def __call__(self, environ, start_response):
        request = Request(environ)
        request.charset = 'utf8'
        http_method = request.params.get('X-HTTP-Method-Override',
                         request.headers.get('X-HTTP-Method-Override', 
                             request.method)).upper()
        method = getattr(self, http_method, None)
        if method is None or not callable(method):
            response = Response(status=405, body="<h1>HTTP Method Not Allowed</h1>")
        else:
            args_re = getattr(method, 'url_map', None)
            args = []
            kwargs = {}
            if args_re is not None:
                match = args_re.match(request.path_info)
                if match is not None:
                    args = match.groups()
                    kwargs = match.groupdict()
            else:
                args = request.path_info.strip('/').split('/')
            response = method(request, *args, **kwargs)
        start_response(response.status, response.headerlist)
        return response.app_iter

class AnyStat(RequestDispatcher):
    def __init__(self):
        self.cache = StatCacher()

    def POST(self, request, db_name, collection_name, name, value):
        print "here3"
        stat =  {   'stat_name': name,
                    'stat_value': value,
                    'stat_datestamp': request.params.get('Date',
                                        request.headers.get('Date', 
                                            datetime.datetime.now())),
                }
        stat.update(request.params.mixed())
        self.cache.add(db_name, collection_name, stat)
        return Response(status=204)

    def GET(self, request, db_name, collection_name, name):
        stats = self.cache.get(db_name, collection_name, stat_name=name)
        return Response(body="<h1>Welcome to AnyStat</h1><pre>%s</pre>"%json.dumps(stats, default=json_util.default, sort_keys=True, indent=4))



def start_server():
    evwsgi.start("0.0.0.0", "5747")
    evwsgi.set_base_module(fapws.base)
    stats_app = AnyStat()
    evwsgi.wsgi_cb(("/stats/", stats_app))
    commit = lambda: stats_app.cache.commit()
    evwsgi.add_timer(10, commit)
    #evwsgi.set_debug(1)
    evwsgi.run()

if __name__ == "__main__":
    start_server()
