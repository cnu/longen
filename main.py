import os
import md5
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
        url_md5 = md5.md5(short_url).hexdigest()
        result = yield gen.Task(c.get, url_md5)
        if result:
            # Get URL from cache
            actual_url = result
        else:
            response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
            if response.error:
                print response.error
                print "Error for %s: %s" %(short_url, str(response.error))
                actual_url = 'Error reading from URL'
            else:
                actual_url = response.effective_url
                yield gen.Task(c.set, url_md5,actual_url)

        self.render("expanded.html", short_url=short_url, actual_url=actual_url)


class ExpandRedirectHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @gen.engine
    def get(self):
        short_url = self.request.arguments['url'][0].strip().encode('ascii')
        url_md5 = md5.md5(short_url).hexdigest()
        result = yield gen.Task(c.get, url_md5)
        if result:
            # Get URL from cache
            actual_url = result
        else:
            response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
            if response.error:
                print "Error for %s: %s" %(short_url, str(response.error))
                actual_url = '/'
            else:
                actual_url = response.effective_url
                yield gen.Task(c.set, url_md5, actual_url)
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