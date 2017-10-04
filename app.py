# i.deskov@pflb.ru
#!flask/bin/python

from flask import Flask, request, make_response, jsonify
import re
import logging
import requests
import config
from jsonpath_ng import jsonpath, parse
import json
import threading
import atexit
import signal

CHECK_TIME = 30 #Seconds

# Queue
tasksQueue = []

# Queue lock
queueLock = threading.Lock()

# backgroung worker
queueWorker = threading.Thread()

boards = []

json_updatedcardid = parse('action.data.card.id')
json_alter_updatedcardid = parse('cards[0].id')
json_updatedchecklist = parse('action.data.checklist.id')
json_label_synchronize = parse("labels[0].id")#"labels[?(@.name == 'Sync')].id"

json_boardids = parse('[*].id')

def createApp():
    app = Flask(__name__)
    
    def interruptWorker(self, signum):
        global queueWorker
        queueWorker.cancel()

    def doStuff():
        global tasksQueue
        global queueWorker
        global boards
        curTask = []
        with queueLock:
        # Do your stuff with commonDataStruct Here
            #app.logger.info(tasksQueue)
            if tasksQueue:
                curTask = tasksQueue.pop(0)
                #app.logger.info(tasksQueue)
        if curTask:
            r = requests.get('https://api.trello.com/1/members/gitlabpflb/boards?fields=id,name&key=' + config.trelloKey + '&token='+config.trelloToken) #fields=id,name,labels
            boardids = json_boardids.find(json.loads(r.text))
            for bid in boardids:
                if bid.value not in boards:
                    rr = requests.get('https://api.trello.com/1/boards/'+bid.value+'/labels?key=' + config.trelloKey + '&token='+config.trelloToken)
                    #resu = jsonpath.jsonpath(json.loads(rr.text), "$.[?(@.name == 'Sync')]")
                    app.logger.info(rr.text)
                    #boards = boards + [bid.value]
            app.logger.info(r.text)
            app.logger.info(boards)
        #boards = 
        
        # Set the next thread to happen
        queueWorker = threading.Timer(CHECK_TIME, doStuff, ())
        queueWorker.start()   

    def doStuffStart():
        # Do initialisation stuff here
        global queueWorker
        # Create your thread
        queueWorker = threading.Timer(CHECK_TIME, doStuff, ())
        queueWorker.start()
    
    # Initiate
    doStuffStart()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    signal.signal(signal.SIGTERM, interruptWorker)
    #atexit.register(interruptWorker)
    return app

#start
app = createApp() 

#log config
@app.before_first_request
def setup_logging():
    if not app.debug:
        # In production mode, add log handler to sys.stderr.
        app.logger.addHandler(logging.StreamHandler())
        app.logger.setLevel(logging.INFO)
        app.logger.info('logger ready')



@app.route('/', methods=['GET'])
def process_get_req():
    app.logger.info(request.data)
    return make_response('Yeah, yeah. I\'m still alive. Don\'t worry.', 200)

@app.route('/', methods=['POST'])
def main():
    global tasksQueue
    app.logger.info(request.data)
    updatedcardid = json_updatedcardid.find(json.loads(request.data))
    updatedcardid = updatedcardid[0].value if updatedcardid else ''
    if not updatedcardid:
        updatedchecklist = json_updatedchecklist.find(json.loads(request.data))
        updatedchecklist = updatedchecklist[0].value if updatedchecklist else ''
        if updatedchecklist:
            app.logger.info('updated checklist: ' + updatedchecklist)
            r = requests.get('https://api.trello.com/1/checklists/'+updatedchecklist+'?fields=name&cards=all&card_fields=name&key=' + config.trelloKey + '&token='+config.trelloToken)
            updatedcardid = json_alter_updatedcardid.find(json.loads(r.text))
            updatedcardid = updatedcardid[0].value if updatedcardid else ''
    if updatedcardid:
        updatedcardinfo = requests.get('https://api.trello.com/1/cards/'+updatedcardid+'?key=' + config.trelloKey + '&token='+config.trelloToken)
        loaded = json.loads(updatedcardinfo.text)
        app.logger.info(updatedcardinfo.text)
        synclabel = list(filter(lambda a: a['name'] == 'Sync',loaded['labels']))
        app.logger.info(synclabel)
        #synclabelid = filter(lambda a: a['name'] == 'Sync' and a['color'] == 'null' ,json.loads(r.text))
        if synclabel:
            app.logger.info(u'Синхронизируемая карточка')
            tasksQueue = tasksQueue + [[updatedcardid,updatedcardinfo.text,request.data]]
        else:
            app.logger.info(u'НЕ синхронизируемая карточка')
    #app.logger.info(r.text)
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
    app.logger.info('Starting web server.')
    app.debug = True
    app.run()
    app.logger.info('Stoped web server.')