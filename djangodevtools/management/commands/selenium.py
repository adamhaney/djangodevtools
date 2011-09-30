# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.conf import settings
from djangodevtools.management.commands.itest import Command as TCommand, \
    TestCommand
from optparse import make_option

class Command(TCommand):
    #Create the option list to facilitate developers
    option_list = TCommand.option_list + (
        make_option('--browser', dest='browser', default="chrome",
            help='Specify browser that perform the navigation.'),    

        #SELENIUM_PORT = 4444
        make_option('--selenium_port', dest='sport', default=4444,
            help='Specify selenium server port. Useful for buildbot.'),
    )
    help = 'Runs selenium server, an wsgi test server and the test suite for the specified applications, or the entire site if no apps are specified.'
    args = TCommand.args + ' --browser [chrome|firefox|opera|explorer] [--sport 4444]'

    def handle(self, *test_labels, **options):
        
        settings.SELENIUM_BROWSER = "*%s" % options.get('browser', "chrome")
        settings.SELENIUM_PORT = options.get('sport', 4444)
        settings.TEST_WSGI_PORT = options.get('http_port', 8888)
        settings.TEST_DB_PREFIX = options.get('db_prefix', "_dev_tools")
        settings.TEST_RUNNER = 'djangodevtools.wsgitest.SeleniumTestRunner'
        
        TestCommand.handle(self, *test_labels, **options)