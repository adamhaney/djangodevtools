# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.commands.test import Command as TestCommand
from optparse import make_option
from django.conf import settings

class Command(TestCommand):
    #Create the option list to facilitate developers
    option_list = TestCommand.option_list + (
        #TEST_WSGI_PORT = 8888
        make_option('--http_port', dest='http_port', default=8888,
            help='Specify django wsgi server port. Useful for concurrent instances of buildbot.'),

        make_option('--reuse_db', dest='reuse_db', default=False,
                help='If true, it will be use the previous backuped db'),

        make_option('--db_suffix', dest='db_suffix', default="_dev_tools",
            help='Specify suffix db name.'),            
    )
    help = 'Runs wsgi test server and the test integration test suite for the specified applications, or the entire site if no apps are specified.'
    args = '[appname ...  ] [--http_port 8888] [--reuse_db True]'

    requires_model_validation = False

    def handle(self, *test_labels, **options):
        settings.TEST_WSGI_PORT = options.pop('http_port', 8888)
        settings.TEST_DB_SUFFIX = options.pop('db_suffix', "_dev_tools")
        settings.REUSE_TEST_DB = options.pop('reuse_db', False)
        if hasattr(settings, 'WSGI_TEST_RUNNER'):
            settings.TEST_RUNNER = settings.WSGI_TEST_RUNNER
        else:
            settings.TEST_RUNNER = 'djangodevtools.wsgitest.TrasactionWsgiTestRunner'
#        #settings.PASSWORD_VALIDITY = None
#        #settings.PASSWORD_ALERT = 80 # days
#        #settings.PASSWORD_FORCE_CHANGE_FIRST_LOGIN = False
        TestCommand.handle(self, *test_labels, **options)