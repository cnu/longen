import os
import traceback

import tornado.ioloop
import tornado.web
from tornado.curl_httpclient import CurlAsyncHTTPClient

settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )

def get_head(url, callback):
    http_client = CurlAsyncHTTPClient()
    http_client.fetch(url.encode('ascii'), callback, method='HEAD')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("main.html")

class ExpandHandler(tornado.web.RequestHandler):
    def handle_request(self, response):
        try:
            if response.error:
                print "Error:", response.error
            else:
                print self.short_url
                actual_url = response.effective_url
                self.render("expanded.html", short_url=self.short_url, actual_url=actual_url)
        except:
            print traceback.format_exc()
    
    @tornado.web.asynchronous
    def get(self):
        print self.request.arguments
        self.short_url = self.request.arguments['url'][0] # TODO: Maybe take in multiple URLs?
        get_head(self.short_url, self.handle_request)


class ExpandRedirectHandler(tornado.web.RequestHandler):
    def handle_redirect_request(self, response):
        try:
            if response.error:
                print "Error:", response.error
            else:
                self.redirect(response.effective_url, permanent=True)
        except:
            print traceback.format_exc()

    @tornado.web.asynchronous
    def get(self):
        try:
            short_url = self.request.arguments['url'][0]
            get_head(short_url, self.handle_redirect_request)
        except:
            print traceback.format_exc()

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