import tornado.ioloop
import tornado.web
from tornado.curl_httpclient import CurlAsyncHTTPClient
# from tornado.httpclient import HTTPRequest
# from tornado.httpclient import HTTPClient
import traceback

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
                actual_url = response.effective_url
                self.render("expanded.html", short_url=self.short_url, actual_url=actual_url)
        except:
            print traceback.format_exc()
    
    @tornado.web.asynchronous
    def get(self, short_url):
        self.short_url = short_url
        get_head(short_url, self.handle_request)


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
    def get(self, short_url):
        try:
            get_head(short_url, self.handle_redirect_request)
        except:
            print traceback.format_exc()

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/e/(.*)", ExpandHandler),
    (r"/expand/(.*)", ExpandHandler),
    (r"/(.*)", ExpandRedirectHandler),
], debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()