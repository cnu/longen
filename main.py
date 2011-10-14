import os
import traceback

import tornado.ioloop
import tornado.web
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado import gen

import brukva

settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )

c = brukva.Client()
c.connect()
http_client = CurlAsyncHTTPClient()

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")

class ExpandHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        short_url = self.request.arguments['url'][0].strip().encode('ascii') # TODO: Maybe take in multiple URLs?
        result = yield gen.Task(c.hgetall, short_url)
        if result:
            # Get URL from cache
            actual_url = result['actual_url']
            hits = result['hits']
            yield gen.Task(c.hincrby, short_url, 'hits', 1)
        else:
            response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
            if response.error:
                print response.error
                print "Error for %s: %s" %(short_url, str(response.error))
                actual_url = 'Error reading from URL'
            else:
                actual_url = response.effective_url
                hits = 1
                yield [gen.Task(c.hset, short_url, 'actual_url', actual_url),
                       gen.Task(c.hset, short_url, 'hits', 1)]

        self.render("expanded.html", short_url=short_url, actual_url=actual_url, hits=hits)


class ExpandRedirectHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        short_url = self.request.arguments['url'][0].strip().encode('ascii')
        response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
        result = yield gen.Task(c.hgetall, short_url)
        if result:
            # Get URL from cache
            actual_url = result['actual_url']
            hits = result['hits']
            yield gen.Task(c.hincrby, short_url, 'hits', 1)
        else:
            response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
            if response.error:
                print "Error for %s: %s" %(short_url, str(response.error))
                actual_url = '/'
            else:
                actual_url = response.effective_url
                yield [gen.Task(c.hset, short_url, 'actual_url', actual_url),
                       gen.Task(c.hset, short_url, 'hits', 1)]
        self.redirect(actual_url, permanent=True)

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/e", ExpandHandler),
    (r"/expand", ExpandHandler),
    (r"/r", ExpandRedirectHandler),
    (r"/redirect", ExpandRedirectHandler),
], debug=True, **settings)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()