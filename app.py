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
json_updatedcardname = parse('action.data.card.name')
json_oldupdatedcardname = parse('action.data.old.name')
json_action = parse('action.display.translationKey')
json_autor = parse('action.display.entities.memberCreator.username')


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
            if curTask[1] == 'action_renamed_card':
                updatedcardname = json_oldupdatedcardname.find(curTask[2])
            else:
                updatedcardname = json_updatedcardname.find(curTask[2])
            updatedcardname = updatedcardname[0].value if updatedcardname else ''
            app.logger.info('updated card name: "%s"' % updatedcardname)
            boardlist = requests.get('https://api.trello.com/1/members/gitlabpflb/boards?fields=id,name' + config.CREDENTIALS_STR) #fields=id,name
            filtered = list(filter(lambda a: a['name'] not in config.BOARD_FILTER ,json.loads(boardlist.text)))
            boardids = [b['id'] for b in filtered]
            for bid in boardids:
                boardlabels = requests.get('https://api.trello.com/1/boards/'+bid+'/labels?' + config.CREDENTIALS_STR)
                loaded = json.loads(boardlabels.text)
                synclabel = list(filter(lambda a: a['name'] == config.SYNC_LABEL_NAME, loaded))
                if synclabel:
                    app.logger.info('Synchronizing with board '+ bid)
                    boardcards = requests.get('https://api.trello.com/1/boards/'+bid+'/cards/?fields=name,id,labels' + config.CREDENTIALS_STR)
                    Synchronizedcard = []
                    Synchronizedcards = list(filter(lambda a: config.SYNC_LABEL_NAME in [l['name'] for l in a['labels']] and a['name'] == updatedcardname,json.loads(boardcards.text)))
                    if Synchronizedcards:
                        for crdid in [c['id'] for c in Synchronizedcards]:
                            app.logger.info('Synchronizind with card '+ crdid)
                            params = {'name': updatedcardname,
                                      'key':config.TRELLO_KEY,
                                      'token':config.TRELLO_TOKEN}
                            resu = requests.put('https://api.trello.com/1/cards/'+ crdid, data = params)
                            app.logger.info(resu.text)
        # Set the next thread to happen
        queueWorker = threading.Timer(config.CHECK_TIME, doStuff, ())
        queueWorker.start()   

    def doStuffStart():
        # Do initialisation stuff here
        global queueWorker
        # Create your thread
        queueWorker = threading.Timer(config.CHECK_TIME, doStuff, ())
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
    #app.logger.info(request.data)
    j = json.loads(request.data)
    action = json_action.find(j)
    action = action[0].value if action else ''
    autor = json_autor.find(j)
    autor = autor[0].value if autor else ''
    updatedcardid = json_updatedcardid.find(j)
    updatedcardid = updatedcardid[0].value if updatedcardid else ''
    if not updatedcardid:
        updatedchecklist = json_updatedchecklist.find(j)
        updatedchecklist = updatedchecklist[0].value if updatedchecklist else ''
        if updatedchecklist:
            app.logger.info('updated checklist: ' + updatedchecklist)
            r = requests.get('https://api.trello.com/1/checklists/'+updatedchecklist+'?fields=name&cards=all&card_fields=name' + config.CREDENTIALS_STR)
            updatedcardid = json_alter_updatedcardid.find(json.loads(r.text))
            updatedcardid = updatedcardid[0].value if updatedcardid else ''
    if updatedcardid:
        app.logger.info('%s did %s on %s' % (autor,action,updatedcardid))
        updatedcardinfo = requests.get('https://api.trello.com/1/cards/'+updatedcardid+'?' + config.CREDENTIALS_STR)
        loaded = json.loads(updatedcardinfo.text)
        synclabel = list(filter(lambda a: a['name'] == config.SYNC_LABEL_NAME,loaded['labels']))
        #app.logger.info(synclabel)
        if synclabel:
            app.logger.info('Synchronized card')
            tasksQueue = tasksQueue + [[updatedcardid,action,j,updatedcardinfo.text]]
        else:
            app.logger.info(u'NOT Synchronized card')
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