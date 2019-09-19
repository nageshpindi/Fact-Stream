import json

import time

import tornado
import tornado.httpserver
import tornado.ioloop
import tornado.web
import sys
import os

from tornado import web

import logging

from multiprocessing import Process
from distutils.util import strtobool
import traceback

import tornado
import logging

from controller import controller


class PDFProcess(web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self):
        data_json=''
        data_json = tornado.escape.json_decode(self.request.body)
        jsonOutput=ctrlr.ProcessData(data_json['input_path'],data_json['output_path'],data_json['baseDataDirectory'])
        dict_status=dict()
        # dict_status['isDone']=status
        dict_status['output'] = jsonOutput
        self.write(json.dumps(dict_status))
        self.finish()



if __name__ == '__main__':
    print('initializing tornado')
    global ctrlr
    ctrlr = controller()

    print('initializing tornado')


    app = tornado.web.Application([(r"/extract", PDFProcess),])

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8005)
    print('tornado is running on port 8005')


    ioloop = tornado.ioloop.IOLoop.instance()
    ioloop.start()
