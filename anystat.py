#! /usr/bin/env python
import re
import httplib
import ordereddict

import pymongo
import fapws._evwsgi as evwsgi
import fapws.base
from webob import Request, Response

connection = pymongo.Connection()

class RequestDispatcher(object):
    def __call__(self, environ, start_response):
        request = Request(environ)
        method = getattr(self, request.method, None)
        if method is None or not callable(method):
            response = Response(status=405, body="<h1>HTTP Method Not Allowed</h1>")
        else:
            try:
                args_re = getattr(method, 'url_args', None)
                if args_re is not None:
                    args = args_re.match(request.path_info).groups()
                else:
                    args = request.path_info.strip('/').split('/')
                response = method(request, args)
            except Exception, e:
                print e
                response = Response(status=500, body="<h1>Server Error</h1>")
        start_response(response.status, response.headerlist)
        return response.app_iter

class AnyStat(RequestDispatcher):
    def GET(self, request, url_pieces):
        return Response(body="<h1>Welcome to AnyStat</h1><pre>%s</pre>"%'\n'.join(url_pieces))



def start_server():
    evwsgi.start("0.0.0.0", "5747")
    evwsgi.set_base_module(fapws.base)
    evwsgi.wsgi_cb(("/stats/", AnyStat()))
    #evwsgi.set_debug(1)
    evwsgi.run()

if __name__ == "__main__":
    start_server()
