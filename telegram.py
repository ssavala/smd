import requests
import datetime
import io, os
import re
import main

import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)-2s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)


class BotHandler(object):

    def __init__(self):
        self.token = '752979930:AAFhdyGx0CSOJ-m17wLGN0NhrxvpwCqCPoQ'
        self.api_url = "https://api.telegram.org/bot{}/".format(self.token)

    def getUpdates(self, offset=None, timeout=30):

        method = 'getUpdates'
        params = {
            'timeout': timeout,
            'offset': offset
        }

        response = requests.get(self.api_url + method, params)

        return response.json()['result']

    def sendText(self, chat_id, text):

        params = {
            'chat_id': chat_id,
            'text': text
        }

        method = 'sendMessage'

        return requests.post(self.api_url + method, params)

    def sendHTML(self, chat_id, text):

        params = {
            'chat_id': chat_id,
            'parse_mode': 'HTML',
            'text': text,
        }

        method = 'sendMessage'

        return requests.post(self.api_url + method, params)


    def sendAudio(self, chat_id, name, artist, audio, thumb):

        method = 'sendAudio'

        files = {
            'audio': audio,
            'thumb':thumb
        }

        data = {
            'chat_id' : chat_id,
            'title': str(name),
            'performer':str(artist),
            'caption':f'<b>{str(artist)}</b> {str(name)}',
            'parse_mode':'HTML'
        }

        response = requests.post(
                        self.api_url + method,
                        files=files,
                        data=data
                    )
        #logging
        logging.info(f'SEND STATUS {response.status_code} {response.reason}')

        return response.status_code

    def sendPhoto(self, chat_id, photo, text):

        method = 'sendPhoto'

        files = {
            'photo': photo
        }

        data = {
            'chat_id' : chat_id,
            'caption':text,
            'parse_mode':'HTML'
        }

        response = requests.post(
                        self.api_url + method,
                        files=files,
                        data=data
                    )
        #logging
        logging.info(f'SEND STATUS {response.status_code} {response.reason}')

        return response.status_code


    def checkLastUpdates(self):

        result = self.getUpdates()

        return result[-1] if len(result) > 0 else None

class Controller(object):

    def __init__(self):
        self.bot = BotHandler()
        self.offset = None

        self.downlader = main.MusicDownloader()


    def classify(self, message):

        if str(message).find('open.spotify.com') > 0:
            return 'link'

        elif str(message).find(':track:') > 0:
            return 'uri'

        elif str(message) == '/start':
            return 'start'

        else:
            return 'text'


    def convertToURI(self, link):
        return "spotify:track:" + str(str(link).split('/')[-1])

    def isIncorrect(self, text):
        r = re.compile("[а-яА-Я]+")
        text = str(text).split(' ')

        return True if len([w for w in filter(r.match, text)]) else False


    def controller(self, message, id):

        type = self.classify(message)

        #logging
        logging.info(f'TYPE [{type}] {message}')

        #start message
        if type == 'start':

            #logging
            logging.info('Sended hello message')

            code = self.bot.sendPhoto(
                chat_id=id,
                photo=open(f"Data/header.png",'rb'),
                text=f'<b>Just share song from the Spotify, or paste Spotify URI.</b>'
            )


            return True


        elif type == 'text':

            state, data =  self.downlader.downloadBySearchQuery(message)

            if state:

                fixed_name = f'{data["artist"][0]} - {data["name"]}'
                fixed_name = fixed_name.replace('.','')
                fixed_name = fixed_name.replace(',','')
                fixed_name = fixed_name.replace("'",'')
                fixed_name = fixed_name.replace("/","")

                if self.isIncorrect(fixed_name):
                    #logging
                    logging.warning(f"Detected incorrect name {fixed_name}")

                    os.rename(
                        f"Downloads/{fixed_name}.mp3",
                        f"Downloads/{data['uri']}.mp3"
                    )
                    #logging
                    logging.info(f"RENAMED TO Downloads/{data['uri']}.mp3")

                    fixed_name = data['uri']

                code = self.bot.sendAudio(
                    chat_id=id,
                    audio=open(f"Downloads/{fixed_name}.mp3",'rb'),
                    thumb=open(f"Downloads/{data['uri']}.png",'rb'),
                    name=f'{data["name"]}',
                    artist=f'{data["artist"][0]}'
                )

                if int(code) != 200:
                    #logging
                    logging.warning(f'CODE {code}')
                    self.bot.sendText(id,text='Something went wrong:(')


                os.remove(f"Downloads/{fixed_name}.mp3")
                #logging
                logging.info(f'DELETED Downloads/{fixed_name}.mp3')

                os.remove(f"Downloads/{data['uri']}.png")
                #logging
                logging.info(f"DELETED Downloads/{data['uri']}.png")


            else:
                #logging
                logging.error(f'SENDED "Couldn\'t find that" MESSAGE')
                self.bot.sendText(id,text='Couldn\'t find that:(')
                return False

            return True


        elif type == 'link':

            #logging
            logging.info(f'Converted open.spotify.com link to spotify URI')

            message = self.convertToURI(message)


        #get data
        uri = str(message).split(':')[-1]
        data = self.downlader.getData(message)

        #logging
        logging.info(f'SONG  {data["artist"][0]} - {data["name"]}')

        #fix name
        fixed_name = f'{data["artist"][0]} - {data["name"]}'
        fixed_name = fixed_name.replace('.','')
        fixed_name = fixed_name.replace(',','')
        fixed_name = fixed_name.replace("'",'')
        fixed_name = fixed_name.replace("/","")

        #logging
        logging.info(f'FIXED {fixed_name}')

        if self.downlader.downloadBySpotifyUri(message):

            if self.isIncorrect(fixed_name):
                #logging
                logging.warning(f"Detected incorrect name {fixed_name}")

                os.rename(
                    f"Downloads/{fixed_name}.mp3",
                    f"Downloads/{uri}.mp3"
                )
                #logging
                logging.info(f"RENAMED TO Downloads/{uri}.mp3")

                fixed_name = uri

            code = self.bot.sendAudio(
                chat_id=id,
                audio=open(f"Downloads/{fixed_name}.mp3",'rb'),
                thumb=open(f"Downloads/{uri}.png",'rb'),
                name=f'{data["name"]}',
                artist=f'{data["artist"][0]}'
            )


            if int(code) != 200:
                #logging
                logging.warning(f'CODE {code}')
                self.bot.sendText(id,text='Something went wrong:(')


            os.remove(f"Downloads/{fixed_name}.mp3")
            #logging
            logging.info(f'DELETED Downloads/{fixed_name}.mp3')

            os.remove(f"Downloads/{uri}.png")
            #logging
            logging.info(f'DELETED Downloads/{uri}.png')

        else:

            #logging
            logging.error(f'SENDED "Something went wrong" MESSAGE')
            self.bot.sendText(id,text='Something went wrong:(')
            return False

        return True



    def mainloop(self):
        while True:

            self.bot.getUpdates(self.offset)

            update = self.bot.checkLastUpdates()

            if update:

                update_id = update['update_id']

                try:
                    chat_id = update['message']['chat']['id']
                    chat_name = update['message']['chat']['first_name']
                    message = update['message']['text']

                    #logging
                    logging.info(f'USER [{chat_name}] {message}')

                except:
                    #logging
                    logging.error('Unsupported message')

                self.controller(message, chat_id)

                self.offset = update_id + 1




if __name__ == '__main__':
    try:
        os.system('pip3 install git+https://github.com/nficano/pytube.git')
    except:pass
    logging.info('Starting app')
    controller = Controller()
    controller.mainloop()