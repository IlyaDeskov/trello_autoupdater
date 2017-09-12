# v 0.1
# m.rogozhnikov@pflb.ru
#!flask/bin/python

from flask import Flask, request, make_response, jsonify
import re
import logging
import requests
import config

#start
app = Flask(__name__)

#log config
@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)
        app.logger.info('logger ready')
        #r = requests.get('https://api.trello.com/1/tokens/'+config.trelloToken+'/webhooks/?key='+config.trelloKey).content path_url
        r = requests.post('https://api.trello.com/1/tokens/'+config.trelloToken+'/webhooks/?key='+config.trelloKey, data = {'description': 'Autoupdater webhook', 'callbackURL': 'https://trello-autoupdater.herokuapp.com/', 'idModel': '555de58432eed35eb238e362'})
        app.logger.info(r.request.body)

#logger = logging.getLogger('Log Trello-autoupdater')
#logger.setLevel(config.logLevel)
#file
#fh = logging.handlers.RotatingFileHandler(config.logFile, maxBytes=102400, backupCount=4, encoding=None)
#fh.setLevel(config.logLevel)
#console
#ch = logging.StreamHandler()
#ch.setLevel(config.logLevel)
#format
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#ch.setFormatter(formatter)
#fh.setFormatter(formatter)
#logger.addHandler(ch)
#logger.addHandler(fh)

@app.route('/', methods=['POST','GET'])
def main():
    app.logger.info(request.data)
    return make_response('OK', 200)

@app.errorhandler(404)
def bad_request(error):
    app.logger.warn('Bad request.')
    return make_response(jsonify({'error': 'Bad request.'}), 404)
# 405
@app.errorhandler(405)
def bad_request(error):
    app.logger.warn('Bad type request.')
    return make_response(jsonify({'error': 'Bad type request.'}), 405)

#config server
if __name__ == "__main__":
    app.logger.info('Started web server.')
    app.debug = True
    app.run()
    app.logger.info('Stoped web server.')