import os
import md5
import logging
import traceback

import tornado.ioloop
import tornado.web
import tornado.options
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado import gen

import brukva

settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
        )
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
c = brukva.Client(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
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
        format = self.request.arguments.get('format', [''])[0].strip()
        logging.info("Expand: %s" % short_url)
        url_md5 = md5.md5(short_url).hexdigest()
        result = yield gen.Task(c.get, url_md5)
        if result:
            # Get URL from cache
            actual_url = result
            logging.info("From Cache")
        else:
            logging.info("From Request")            
            response = yield gen.Task(http_client.fetch, short_url, method='HEAD')
            if response.error:
                logging.error(response.error)
                logging.error("Error for %s: %s" %(short_url, str(response.error)))
                actual_url = 'Error reading from URL'
            else:
                actual_url = response.effective_url
                yield gen.Task(c.set, url_md5,actual_url)
        if format == 'text':
            self.set_header("Content-Type", "text/plain")
            self.write(actual_url)
            self.finish()
        else:
            self.render("expanded.html", short_url=short_url, actual_url=actual_url)


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/e", ExpandHandler),
    (r"/expand", ExpandHandler),
], debug=True, **settings)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8888))
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()
