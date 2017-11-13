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


json_updatedCardID = parse('action.data.card.id')
json_alter_updatedCardID = parse('cards[0].id')
json_updatedChecklist = parse('action.data.checklist.id')
json_updatedCardName = parse('action.data.card.name')
json_oldUpdatedCardName = parse('action.data.old.name')
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
            #app.logger.info(tasksQueue)
            if tasksQueue:
                curTask = tasksQueue.pop(0)
                #app.logger.info(tasksQueue)
        if curTask:
            if curTask[1] == 'action_renamed_card':
                updatedCardName = json_oldUpdatedCardName.find(curTask[2])
                newName = json_updatedCardName.find(curTask[2])
            else:
                updatedCardName = json_updatedCardName.find(curTask[2])
                newName = updatedCardName
            updatedCardName = updatedCardName[0].value if updatedCardName else ''
            newName = newName[0].value if newName else ''
            cardInfoDict = json.loads(curTask[3])
            updatedCardLabels = [l['name'] for l in cardInfoDict['labels']]
            app.logger.info(updatedCardLabels)
            updatedCardDescription = cardInfoDict['desc']
            #updatedCardDescription = 
            app.logger.info('updated card name: "%s"' % updatedCardName)
            boardList = requests.get('https://api.trello.com/1/members/gitlabpflb/boards?fields=id,name' + config.CREDENTIALS_STR) #fields=id,name
            filtered = list(filter(lambda a: a['name'] not in config.BOARD_FILTER ,json.loads(boardList.text)))
            boardIDs = [b['id'] for b in filtered]
            for bid in boardIDs:
                boardLabels = requests.get('https://api.trello.com/1/boards/'+bid+'/labels?' + config.CREDENTIALS_STR)
                boardLabels = json.loads(boardLabels.text)
                boardLabels = dict([(l['name'],l['id'])for l in boardLabels])
                syncLabel = list(filter(lambda a: a == config.SYNC_LABEL_NAME, boardLabels))
                boardLists = requests.get('https://api.trello.com/1/boards/'+bid+'/lists?' + config.CREDENTIALS_STR)
                boardLists = json.loads(boardLists.text)
                boardLists = dict([(l['id'],l['name'])for l in boardLists])
                boardListsFilter = dict(list(filter(lambda a : any([bool(re.match(reg,a[1])) for reg in config.LIST_FILTER]),boardLists.items())))
                if syncLabel:
                    app.logger.info('Synchronizing with board '+ bid)
                    boardCards = requests.get('https://api.trello.com/1/boards/'+bid+'/cards/?fields=name,id,labels,idList' + config.CREDENTIALS_STR)
                    synchronizedCard = []
                    synchronizedCards = list(filter(lambda a: config.SYNC_LABEL_NAME in [l['name'] for l in a['labels']]
                                                               and a['name'] == updatedCardName
                                                               and a['idList'] not in boardListsFilter,json.loads(boardCards.text)))
                    #app.logger.info(list(filter(lambda a: a['name'] in updatedCardLabels,synchronizedCards[0]['labels'])))
                    app.logger.info(synchronizedCards)
                    
                    if synchronizedCards:
                        for crdid in [c['id'] for c in synchronizedCards]:
                            app.logger.info('Synchronizing with card '+ crdid)
                            labelsToAdd = []
                            labelsToCreate = []
                            for a in list(filter(lambda a: a != config.SYNC_LABEL_NAME,updatedCardLabels)):
                                if a in boardLabels:
                                    labelsToAdd = labelsToAdd + [boardLabels[a]]
                                else:
                                    labelsToCreate = labelsToCreate + [a]
                            app.logger.info(labelsToCreate)
                            app.logger.info(cardInfoDict['labels'])
                            #if labelsToCreate:
                            #    for ll in labelsToCreate:
                                    
                                    #createdLabel = requests.post('https://api.trello.com/1/labels?' + config.CREDENTIALS_STR, params = {'name':ll,'color':,'idBoard':bid})
                            app.logger.info(curTask[3])
                            queryString = {'name'    :   newName,
                                           'desc'    :   updatedCardDescription,
                                           'key'     :   config.TRELLO_KEY,
                                           'token'   :   config.TRELLO_TOKEN,
                                           'idLabels':   ','.join(labelsToAdd)}
                            resu = requests.request("PUT", 'https://api.trello.com/1/cards/'+ crdid, params=queryString)
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
    j = json.loads(request.data)
    #app.logger.info(j)
    action = json_action.find(j)
    action = action[0].value if action else ''
    autor = json_autor.find(j)
    autor = autor[0].value if autor else ''
    updatedCardID = json_updatedCardID.find(j)
    updatedCardID = updatedCardID[0].value if updatedCardID else ''
    if not updatedCardID:
        updatedChecklist = json_updatedChecklist.find(j)
        updatedChecklist = updatedChecklist[0].value if updatedChecklist else ''
        if updatedChecklist:
            app.logger.info('updated checklist: ' + updatedChecklist)
            r = requests.get('https://api.trello.com/1/checklists/'+updatedChecklist+'?fields=name&cards=all&card_fields=name' + config.CREDENTIALS_STR)
            updatedCardID = json_alter_updatedCardID.find(json.loads(r.text))
            updatedCardID = updatedCardID[0].value if updatedCardID else ''
    if updatedCardID:
        app.logger.info('%s did %s on %s' % (autor,action,updatedCardID))
        updatedCardInfo = requests.get('https://api.trello.com/1/cards/'+updatedCardID+'?' + config.CREDENTIALS_STR)
        loaded = json.loads(updatedCardInfo.text)
        syncLabel = list(filter(lambda a: a['name'] == config.SYNC_LABEL_NAME,loaded['labels']))
        #app.logger.info(syncLabel)
        if syncLabel:
            app.logger.info('Synchronized card')
            tasksQueue = tasksQueue + [[updatedCardID,action,j,updatedCardInfo.text]]
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