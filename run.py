from logging import basicConfig, FileHandler, DEBUG
from os import path, chdir

from whatsapp import WhatsApp

if __name__ == "__main__":
    chdir(path.dirname(__file__))
    basicConfig(handlers=[FileHandler(encoding='utf-8', filename='whatsapp.log', mode='w')],
                level=DEBUG, format=u'%(levelname)s - %(name)s - %(asctime)s: %(message)s')
    whatsapp = WhatsApp(session="mysession")
    whatsapp.run_bot()
