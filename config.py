############################################################
# v 0.1
# m.rogozhnikov@pflb.ru
# Config file

import logging

#https://trello.com/app-key
trelloKey = '59e33cebad55b7425df537d6a060e781'
#https://trello.com/1/connect?key= trelloKey &name=trellogitlab&response_type=token&scope=read,write&expiration=never
trelloToken = 'a2e64fa49cb7ccc2f7f706eb2282d0867e1e9f901b966fe63d0db16a67c3bd1c'
boardName ='MyDemo'
#if you want
creatNewCard = False

#gitlabUrl = "http://192.168.20.249:9000/"
gitlabUrl = "http://127.0.0.1:9000/"

appPort = 80
#appHost = '192.168.20.249'
appHost = '127.0.0.1'

logFile = './trello_autoupdater.log'
logLevel= logging.INFO