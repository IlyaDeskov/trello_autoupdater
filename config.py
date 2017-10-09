############################################################
# v 0.1
# m.rogozhnikov@pflb.ru
# Config file

import logging

#https://trello.com/app-key
TRELLO_KEY = '59e33cebad55b7425df537d6a060e781'
#https://trello.com/1/connect?key= trelloKey &name=trellogitlab&response_type=token&scope=read,write&expiration=never
TRELLO_TOKEN = 'a2e64fa49cb7ccc2f7f706eb2282d0867e1e9f901b966fe63d0db16a67c3bd1c'

CREDENTIALS_STR = '&key=' + TRELLO_KEY + '&token='+TRELLO_TOKEN
BOARD_NAME = u'ИПР Template LT'

SYNC_LABEL_NAME = 'Sync'
CHECK_TIME = 30 #Seconds

BOARD_FILTER = [BOARD_NAME,'MyDemo','UXCrowd',u'Развитие направления НТ']
LIST_FILTER = ['IN PROGRESS','.*DONE.*'] #reg expressions accepted
