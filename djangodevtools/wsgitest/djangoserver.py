'''
Created on Oct 15, 2010

@author: aldaran
'''
from cherrypy.wsgiserver import CherryPyWSGIServer, WSGIPathInfoDispatcher
from django.conf import settings
from django.contrib import admin
from django.core.handlers.wsgi import WSGIHandler
from mediahandler import MediaHandler
import os
import threading


class DjangoThread(threading.Thread):
    """Django server control thread."""
    def __init__(self, **kwargs):
        """Initialize CherryPy Django web server."""
        super(DjangoThread, self).__init__()
        self.options = {'host': 'localhost', 'port': 8888, 'threads': 10,
            'request_queue_size': 15}
        self.options.update(**kwargs)
        self.setDaemon(True)

    def run(self):
        """Launch CherryPy Django web server."""
        server = CherryPyWSGIServer(
            (self.options['host'], int(self.options['port'])),
            WSGIPathInfoDispatcher({
                '/': WSGIHandler(),
                settings.ADMIN_MEDIA_PREFIX: MediaHandler(
                    os.path.join(admin.__path__[0], 'media'))
            }),
            int(self.options['threads']), self.options['host'],
            request_queue_size=int(self.options['request_queue_size']))
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()