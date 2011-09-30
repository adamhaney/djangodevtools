
from django.conf import settings
from django.core.management import setup_environ
from django.db.models import get_app, get_apps
from django.test import TestCase
from django.test.simple import DjangoTestSuiteRunner
from django.test.simple import reorder_suite, build_test, build_suite, DjangoTestRunner, DjangoTestSuiteRunner

from django.db.models.loading import get_app, get_apps
from django.test.utils import setup_test_environment, teardown_test_environment
from django.utils.importlib import import_module
from subprocess import Popen
import os
import unittest


if not hasattr(settings, 'SETTINGS_MODULE'):
    settings.configure()
else:
    PROJECT_PATH = setup_environ(import_module(settings.SETTINGS_MODULE),
        settings.SETTINGS_MODULE)

# compatibility with windows
try:
    from signal import SIGHUP
    def kill_process_tree(process):
        return os.kill(process.pid, SIGHUP)
except:
    def kill_process_tree(process):
        """kill function for Win32"""
        return Popen("taskkill /F /T /PID %i"%process.pid , shell=True).communicate()

DSTEST_PATH = os.path.dirname(__file__)

from djangoserver import DjangoThread
from multidb import MultiTestDB

#TEST_MODULE = getattr(settings, 'WSGI_TEST_MODULE', 'tests.itest')

#def get_wsgi_tests(app_module):
#    try:
#
#        app_path = app_module.__name__.split('.')[:-1]
#        test_module = __import__('.'.join(app_path + [TEST_MODULE]), {}, {}, TEST_MODULE)
#    except ImportError, e:
#        # Couldn't import tests.py. Was it due to a missing file, or
#        # due to an import error in a tests.py that actually exists?
#        import os.path
#        from imp import find_module
#        try:
#            mod = find_module(TEST_MODULE, [os.path.dirname(app_module.__file__)])
#        except ImportError:
#            # 'tests' module doesn't exist. Move on.
#            test_module = None
#        else:
#            # The module exists, so there must be an import error in the
#            # test module itself. We don't need the module; so if the
#            # module was a single file module (i.e., tests.py), close the file
#            # handle returned by find_module. Otherwise, the test module
#            # is a directory, and there is nothing to close.
#            if mod[0]:
#                mod[0].close()
#            raise
#    return test_module
#
#class TrasactionWsgiTestRunner(object):
#    def __init__(self, verbosity=1, interactive=True, failfast=True, **kwargs):
#        self.verbosity = verbosity
#        self.interactive = interactive
#        self.failfast = failfast
#
#    def setup_test_environment(self, **kwargs):
#        setup_test_environment()
#        settings.DEBUG = False
##        defaults = {}
##        if hasattr(settings, 'TEST_WSGI_HOST'):
##            defaults['host'] = settings.TEST_WSGI_HOST
##        if hasattr(settings, 'TEST_WSGI_PORT'):
##            defaults['port'] = settings.TEST_WSGI_PORT
##        django_server = DjangoThread(**defaults)
##        django_server.start()
#
#    def build_suite(self, test_labels, extra_tests=None, **kwargs):
#        suite = unittest.TestSuite()
#        from django.test import simple
#        simple.get_tests = get_wsgi_tests
#        if test_labels:
#            for label in test_labels:
#                if '.' in label:
#                    suite.addTest(simple.build_test(label))
#                else:
#                    app = get_app(label)
#                    suite.addTest(simple.build_suite(app))
#        else:
#            for app in get_apps():
#                suite.addTest(simple.build_suite(app))
#
#        if extra_tests:
#            for test in extra_tests:
#                suite.addTest(test)
#
#        return simple.reorder_suite(suite, (unittest.TestCase,))
#
#    def setup_databases(self, **kwargs):
#        from django.db import connections
#        old_names = []
#        mirrors = []
#        for alias in connections:
#            connection = connections[alias]
#            # If the database is a test mirror, redirect it's connection
#            # instead of creating a test database.
#            if connection.settings_dict['TEST_MIRROR']:
#                mirrors.append((alias, connection))
#                mirror_alias = connection.settings_dict['TEST_MIRROR']
#                connections._connections[alias] = connections[mirror_alias]
#            else:
#                old_names.append((connection, connection.settings_dict['NAME']))
#                connection.creation.create_test_db(self.verbosity, autoclobber=not self.interactive)
#        print 11111111, old_names, mirrors
#        return old_names, mirrors
#
#    def run_suite(self, suite, **kwargs):
#        from django.test.simple import DjangoTestRunner
#        return DjangoTestRunner(verbosity=self.verbosity, failfast=self.failfast).run(suite)
#
#    def teardown_databases(self, old_config, **kwargs):
#        from django.db import connections
#        old_names, mirrors = old_config
#        # Point all the mirrors back to the originals
#        for alias, connection in mirrors:
#            connections._connections[alias] = connection
#        # Destroy all the non-mirror databases
#        for connection, old_name in old_names:
#            connection.creation.destroy_test_db(old_name, self.verbosity)
#
#    def teardown_test_environment(self, **kwargs):
#        teardown_test_environment()
#
#    def suite_result(self, suite, result, **kwargs):
#        return len(result.failures) + len(result.errors)
#
#    def run_tests(self, test_labels, extra_tests=None, **kwargs):
#        """
#        Run the unit tests for all the test labels in the provided list.
#        Labels must be of the form:
#         - app.TestClass.test_method
#            Run a single specific test method
#         - app.TestClass
#            Run all the test methods in a given class
#         - app
#            Search for doctests and unittests in the named application.
#
#        When looking for tests, the test runner will look in the models and
#        tests modules for the application.
#
#        A list of 'extra' tests may also be provided; these tests
#        will be added to the test suite.
#
#        Returns the number of tests that failed.
#        """
#        self.setup_test_environment()
#        suite = self.build_suite(test_labels, extra_tests)
#        old_config = self.setup_databases()
#        result = self.run_suite(suite)
#        self.teardown_databases(old_config)
#        self.teardown_test_environment()
#        return self.suite_result(suite, result)

class TrasactionWsgiTestRunner(DjangoTestSuiteRunner):
    def __init__(self, verbosity=1, interactive=True, failfast=False, **kwargs):
        DjangoTestSuiteRunner.__init__(self,  verbosity, interactive, failfast, **kwargs)
        self.test_module = getattr(settings, 'WSGI_TEST_MODULE', 'tests.itest')
        self.db_prefix = getattr(settings, "DB_PREFIX", '_TESTDB')
        self.reuse_db = getattr(settings, "REUSE_TEST_DB", False)
        self.wsgi_starts = getattr(settings, "TEST_WSGI_START", True)
        from django.test import simple
        simple.TEST_MODULE = self.test_module

        print 'Starting django wsgi server.'
        defaults = {}
        if hasattr(settings, 'TEST_WSGI_HOST'):
            defaults['host'] = settings.TEST_WSGI_HOST
        if hasattr(settings, 'TEST_WSGI_PORT'):
            defaults['port'] = settings.TEST_WSGI_PORT
        django_server = DjangoThread(**defaults)
        django_server.start()



class WsgiTestRunner(object):

    def __init__(self, verbosity=0, interactive=False, failfast=False):
        self.verbosity = verbosity
        self.interactive = interactive
        self.failfast = failfast
        self.test_module = getattr(settings, 'WSGI_TEST_MODULE', 'tests.itest')
        self.db_prefix = getattr(settings, "DB_PREFIX", '_TESTDB')
        self.reuse_db = getattr(settings, "REUSE_TEST_DB", False)
        self.wsgi_starts = getattr(settings, "TEST_WSGI_START", True)
        # Obtain a database test handler.
        self.testdb = self._get_database_wrapper()

    def _get_database_wrapper(self):
        return MultiTestDB(self.db_prefix, self.reuse_db, verbosity=self.verbosity)

    def get_tests(self, test_labels=None):
        from django.test import simple
        simple.TEST_MODULE = self.test_module

        suite = self.testdb.FixtureTestSuiteFactory()

        if test_labels:
            for label in test_labels:
                if '.' in label:
                    suite.addTest(build_test(label))
                else:
                    app = get_app(label)
                    suite.addTest(build_suite(app))
        else:
            for app in get_apps():
                suite.addTest(build_suite(app))

        return reorder_suite(suite, (TestCase,))

    def setup_test_environment(self):
        self.testdb.initialize_test_db()
        if self.wsgi_starts:
            print 'Starting django wsgi server.'
            defaults = {}
            if hasattr(settings, 'TEST_WSGI_HOST'):
                defaults['host'] = settings.TEST_WSGI_HOST
            if hasattr(settings, 'TEST_WSGI_PORT'):
                defaults['port'] = settings.TEST_WSGI_PORT
            django_server = DjangoThread(**defaults)
            django_server.start()

        setup_test_environment()
        settings.DEBUG = False

    def teardown_test_environment(self):
        teardown_test_environment()
        self.testdb.drop()

    def run_tests(self, test_labels):
        suite = self.get_tests(test_labels)

        if suite:
            self.setup_test_environment()
            result = unittest.TextTestRunner(verbosity=self.verbosity).run(suite)
            self.teardown_test_environment()
            return len(result.failures) + len(result.errors)

        else:
            return "Tests not found..."

#from selenium_runner import SeleniumTestRunner