from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.httpserver import HTTPServer
from tornado.options import options
from tornado.log import enable_pretty_logging

from handlers.PagerDutyHandler import PagerDutyHandler
import argparse
import opt

application = Application(
    [
        (r'/PagerDutyNotification', PagerDutyHandler),
    ]
)


def main():
    enable_pretty_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8000)
    args = parser.parse_args()

    http_server = HTTPServer(application)
    http_server.listen(args.port, address='0.0.0.0')
    IOLoop.instance().start()


if __name__ == '__main__':
    main()
