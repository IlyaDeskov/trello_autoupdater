# v 0.1
# m.rogozhnikov@pflb.ru
#!flask/bin/python

from flask import Flask, request, make_response, jsonify
import re
import logging.handlers
import requests
import config

#start
app = Flask(__name__)

#log config
logger = logging.getLogger('Log Trello-autoupdater')
logger.setLevel(config.logLevel)
#file
fh = logging.handlers.RotatingFileHandler(config.logFile, maxBytes=102400, backupCount=4, encoding=None)
fh.setLevel(config.logLevel)
#console
ch = logging.StreamHandler()
ch.setLevel(config.logLevel)
#format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(fh)

@app.route('/', methods=['POST'])
def main():
    logger.info(request)
    return make_response('OK', 200)

@app.errorhandler(404)
def bad_request(error):
    logger.warn('Bad request.')
    return make_response(jsonify({'error': 'Bad request.'}), 404)
# 405
@app.errorhandler(405)
def bad_request(error):
    logger.warn('Bad type request.')
    return make_response(jsonify({'error': 'Bad type request.'}), 405)

#config server
if __name__ == "__main__":
    logger.info('Started web server.')
    app.debug = True
    app.run()
    logger.info('Stoped web server.')