'''
Created on Oct 15, 2010

@author: aldaran
'''
from djangodevtools.wsgitest import PROJECT_PATH
from django.conf import settings
from django.core.management import call_command
from django.db import connections
import os
import shutil
import unittest
from django.core import mail
import logging 

logger = logging.getLogger("tests.djangodevtools")

class MultiTestDB(object):
    """Encapsulate fixtured database handling for tests to be used by
    Django web server. As the Django connection is global, this class will
    setup TEST_DB_NAME as the database in use."""

    def __init__(self, db_prefix="_TESTDB", reuse_backup_if_exist=False, verbosity=0):
        """Initialize MultiTestDB."""
        self.db_prefix = db_prefix
        self.verbosity = verbosity
        
        # modify database name for use different in testing
        for db in settings.DATABASES.values():
            db['NAME'] = db['NAME'] + self.db_prefix
            
        self.reuse_backup_if_exist = reuse_backup_if_exist

    def FixtureTestSuiteFactory(self):
        testdb = self
        class FixtureTestSuite(unittest.TestSuite):
            def add_fixtures(self, ctest):
                """Monkeypatch selenium tests to add django fixtures."""
            
                def test_setup(funct, fixtures):
                    """Test setUp decorator to add fixture reloading."""
            
                    def decorated_setup():
                        """Decorated test setup."""
                        logger.info("Decorated test setup. %s", fixtures)                        
                        testdb.reload_db(fixtures)
                        # reset django test mailbox
                        mail.outbox = []
                        funct()
                    return decorated_setup
                
                def recursive_setup(x):
                    if hasattr(x, "setUp") and hasattr(x, "fixtures"):
                        x.setUp = test_setup(x.setUp, x.fixtures)
                    
                    if hasattr(x, "_tests"):
                        for y in x._tests:
                            recursive_setup(y)
                
                recursive_setup(ctest)
    
            def addTest(self, test):
                self.add_fixtures(test)
                super(FixtureTestSuite, self).addTest(test)
        return FixtureTestSuite()
    
    def initialize_test_db(self):
        """Establish a connection to a fresh TEST_DB_NAME database with the
        test fixtures on it."""
        for key, db in settings.DATABASES.items():
            connection = connections[key]
            name = db['NAME']
            db['SUPPORTS_TRANSACTIONS'] = connection.creation._rollback_works()
            if not self.reuse_backup_if_exist:
                call_command('zap', destroy=True, interactive=False, database=key)
                connection.close()
            
                # If sqlite3 or Postgres is used, create a backup database to speed up
                if db['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
                    # connection.creation is used to overcome transaction management,
                    # allowing to execute DROP and CREATE db commands.
                    cursor = connection.cursor() #@UndefinedVariable
                    connection.creation.set_autocommit() #@UndefinedVariable
                    cursor.execute("DROP DATABASE IF EXISTS %s_backup" % name)
                    cursor.execute("CREATE DATABASE %s_backup WITH TEMPLATE %s" % (name, name))
                    connection.close()
                if db['ENGINE'] == 'django.db.backends.sqlite3':
                    db_path = os.path.join(PROJECT_PATH, name)
                    db_backup_path = '%s.bck' % db_path 
                    shutil.copyfile(db_path, db_backup_path)
            else:
                if db['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
                    # Establish a temporal connection to template1 database and
                    # recreate TEST_DB_NAME.
                    connection.settings_dict["DATABASE_NAME"] = 'template1'
                    cursor = connection.cursor() #@UndefinedVariable
                    connection.creation.set_autocommit() #@UndefinedVariable
                    cursor.execute("DROP DATABASE IF EXISTS %s" % name)
                    cursor.execute("CREATE DATABASE %s WITH TEMPLATE %s_backup" % (name, name))
                    connection.close() #@UndefinedVariable
                    # Change the connection to the new test database.
                    connection.settings_dict["DATABASE_NAME"] = name
                if db['ENGINE'] == 'django.db.backends.sqlite3':
                    db_path = os.path.join(PROJECT_PATH, name)
                    db_backup_path = '%s.bck' % db_path 
                    shutil.copyfile(db_backup_path, db_path)    


    def extra_init(self):
        """Hook for doing any extra initialization. After subclassing TestDB,
        and overriding this method, initialize_test_db will call it."""
        pass

    def reload_db(self, fixtures):
        """Reload fixtures into test database. This is a database dependant
        method. For now, only works on Postgres."""
        
        fix  = [f for f in fixtures if f.find("::")==-1]
        other_fix  = [f for f in fixtures if not f.find("::")==-1]
        for key, db in settings.DATABASES.items():
            connection = connections[key]
            name = db['NAME']
            connection.close() #@UndefinedVariable

            if db['ENGINE'] == 'django.db.backends.sqlite3':
                db_path = os.path.join(PROJECT_PATH, name)
                db_backup_path = '%s.bck' % db_path 
                shutil.copyfile(db_backup_path, db_path)
                
            if db['ENGINE'] == 'django.db.backends.postgresql_psycopg2':
                # Establish a temporal connection to template1 database and
                # recreate TEST_DB_NAME.
                connection.settings_dict["DATABASE_NAME"] = 'template1'
                cursor = connection.cursor() #@UndefinedVariable
                connection.creation.set_autocommit() #@UndefinedVariable
                cursor.execute("DROP DATABASE IF EXISTS %s" % name)
                cursor.execute("CREATE DATABASE %s WITH TEMPLATE %s_backup" % (name, name))
                connection.close() #@UndefinedVariable
                # Change the connection to the new test database.
                connection.settings_dict["DATABASE_NAME"] = name
                
            # Get a cursor (even though we don't need one yet). This has
            # the side effect of initializing the test database.   
            connection.cursor() #@UndefinedVariable
            cfix  = [f.split("::")[-1] for f in other_fix if f.split("::")[0] == key]
            call_command('loaddata', *cfix, commit=True, verbosity=1, database=key)
            connection.close()
        
        call_command('loaddata', *fix, commit=True, verbosity=1)
        return True

    def drop(self):
        """Drop test database. This is a database dependant method. For now,
        only works on Postgres."""
        for key, db in settings.DATABASES.items():
            if db['ENGINE'] in ['django.db.backends.sqlite3', 'django.db.backends.postgresql_psycopg2']:
                if not self.reuse_backup_if_exist:
                    connection = connections[key]
                    name = db['NAME']
            
                    def drop_db(name):
                        """TestDB.drop helper function"""
                        try:
                            connection.creation._destroy_test_db(name, verbosity=0) #@UndefinedVariable
                        except:
                            return None
                        return True
                    connection.close() #@UndefinedVariable
        
                    drop_db('%s_backup' % name)
                    drop_db(name)