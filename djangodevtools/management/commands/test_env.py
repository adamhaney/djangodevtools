# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand, CommandError
from django.db.models.loading import get_app, get_apps
from django.test.simple import get_tests
import unittest
from django.core.management import call_command


class Command(BaseCommand):
    '''
    This command is to help to build test fixtures.
        - zap the database
        - load the fixtures for the passed testcase
        - runserver
    '''
    #option_list = BaseCommand.option_list 

    def handle(self, *args, **options):
        if len(args) < 1 :
            raise CommandError("need at least one unit test TestClass")
        verbosity = int(options.get('verbosity', 0))

        call_command('zap', noinput = False, verbosity = verbosity, load_initial_data = False)
#        for app in get_apps():
#            call_command('sqlsequencereset', app)
        
        for test in args:
            parts = test.split('.')
            if len(parts) != 2:
                raise ValueError("Test label '%s' should be of the form app.TestCase or app.TestCase.test_method" % test)
            app_module = get_app(parts[0])
            test_module = get_tests(app_module)
            TestClass = getattr(app_module, parts[1], None)
            if TestClass is None:
                if test_module:
                    TestClass = getattr(test_module, parts[1], None)
            
            if issubclass(TestClass, unittest.TestCase):
                for f in TestClass.fixtures:
                    if verbosity > 0:
                        print "Looking for fixture `%s`" % f
                    call_command('xloaddata', f, verbosity = verbosity)

        #call_command('runserver', verbosity = verbosity)




