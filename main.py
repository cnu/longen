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
        self.write("longen urls")

class ExpandHandler(tornado.web.RequestHandler):
    def handle_request(self, response):
        try:
            if response.error:
                print "Error:", response.error
            else:
                print response.effective_url
                self.write(response.effective_url)
                print response.body
        except:
            print traceback.format_exc()
        self.finish()
    
    @tornado.web.asynchronous
    def get(self, short_url):
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
    (r"/(.*)", ExpandRedirectHandler),
], debug=True)

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()