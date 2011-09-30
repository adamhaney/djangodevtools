# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import NoArgsCommand, BaseCommand, make_option
from django.core.management.color import color_style
from django.db import connections
from django.db.backends.creation import BaseDatabaseCreation
import datetime
import os
import time
from django.db.utils import DEFAULT_DB_ALIAS

ORACLE_ZAP = """
 begin
  for rec in (select 'drop view '||view_name statement from user_views) loop
    execute immediate rec.statement;
  end loop;
  
  for rec in (select 'drop table '||table_name || ' cascade constraints' statement from user_tables) loop
    execute immediate rec.statement;
  end loop;
  
  for rec in (select 'drop  ' || decode (object_type,'FUNCTION','function ','PACKAGE', 'package ', 'procedure ') ||object_name statement from  user_objects where object_name not like 'BIN$%' and 
object_type in ('FUNCTION','PROCEDURE', 'PACKAGE') ) loop
    execute immediate rec.statement;
  end loop;
  
  for rec in (select 'drop sequence '||sequence_name statement from user_sequences) loop
    execute immediate rec.statement;
  end loop;
  
  for rec in (select 'drop synonym '||synonym_name statement from user_synonyms) loop
    execute immediate rec.statement;
  end loop;
  
  for rec in (select 'drop type '||type_name || ' FORCE' statement from user_types) loop
    execute immediate rec.statement;
  end loop;
end;
"""

class Command(BaseCommand, BaseDatabaseCreation):
    #Create the option list to facilitate developers
    option_list = NoArgsCommand.option_list + (
        make_option('--database', dest='database', default='default',
            help='Database name'),
        make_option('--destroy', action='store_true', dest='destroy', default=False,
            help='Fully destroy and recreate database'),
        make_option('--interactive', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
    )
    help = "Destroy and recreate the database."    
    
    def __init__(self):
        self.style = color_style()

    def swicth_to(self, dbname, verbosity):
        '''
        This function stores original database name in a variable and sets temporary database name as current
        '''
        if verbosity > 0:
            print "Switching to database %s" % dbname        
        self.connection.close()
        old, settings.DATABASES[self.dbname]['NAME'] = settings.DATABASES[self.dbname]['NAME'], dbname        
        self.connection.settings_dict["DATABASE_NAME"] = dbname   
        return settings.DATABASES[self.dbname]['NAME'], old
    
    def create_db(self, dbname, verbosity):
        '''
        This function creates a database with specified name
        '''
        if verbosity > 0:
            print "Creating temp database %s" % dbname           
        suffix = self.sql_table_creation_suffix()
        qn = self.connection.ops.quote_name
        cursor = self.connection.cursor()
        self.set_autocommit()
        if settings.DATABASES[self.dbname]['ENGINE']=='django.db.backends.sqlite3':
            import sqlite3
            try:
                sqlite3.connect(dbname)
            except:
                raise Exception("nable to open database file [%s]" % dbname)
        else:    
            cursor.execute("CREATE DATABASE %s %s" % (qn(dbname), suffix))
        
    def drop_db(self, dbname, verbosity):
        '''
        This function drops specified database
        '''
        if verbosity > 0:
            print "Destroy database %s" % dbname
        cursor = self.connection.cursor()
        self.set_autocommit()
        time.sleep(1) # To avoid "database is being accessed by other users" errors.
        if settings.DATABASES[self.dbname]['ENGINE'] in ['django.db.backends.sqlite3', 'sqlite3']:
            if os.path.exists(dbname):
                os.remove(dbname)
        elif settings.DATABASES[self.dbname]['ENGINE'] in ['django.db.backends.oracle','oracle']:
            cursor.execute( ORACLE_ZAP )
            # Oracle 10.x move table to recyclebin, so we clean it
            try:
                cursor.execute( "purge recyclebin;" )
            except:
                pass
        else:    
            cursor.execute("DROP DATABASE %s" % self.connection.ops.quote_name(dbname))
        self.connection.close()
    
    def recreate_db(self, verbosity):
        '''
        This function :
            1.    creates a temporary database with timestamp as name
            2.    drops the original one
            3.    creates a database with the original one's name 
            4.    drops the temporary one
        The result is an empty version of the original database.
        '''
        print "Zapping....."
        try:
            original_dbname = settings.DATABASES[self.dbname]['NAME']
            original_test_dbname = settings.TEST_DATABASE_NAME            
            if settings.DATABASES[self.dbname]['ENGINE']=='django.db.backends.sqlite3':
                dbPath= settings.DATABASES[self.dbname]['NAME'][:settings.DATABASES[self.dbname]['NAME'].rfind("/")]
                dbPath =  os.path.realpath(settings.DATABASES[self.dbname]['NAME'])
                settings.TEST_DATABASE_NAME = tempdbname = dbPath+"_"+datetime.datetime.now().strftime('%Y%m%d%H%M%S')+".db"
            else:
                settings.TEST_DATABASE_NAME = tempdbname = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            self.create_db(tempdbname, verbosity )
            self.swicth_to(tempdbname, verbosity)
            
            self.drop_db(original_dbname, verbosity )
            self.create_db(original_dbname, verbosity )
            self.swicth_to(original_dbname, verbosity)
            self.drop_db(tempdbname, verbosity )
        finally:
            settings.DATABASES[self.dbname]['NAME'] = original_dbname
            settings.TEST_DATABASE_NAME = original_test_dbname

    def get_drop_table_statement(self, tablename):
        '''
        This function returns the Sql command for table dropping according to database dialect
        '''
        engine = str( settings.DATABASES[self.dbname]['ENGINE'] )
        if engine == 'postgresql_psycopg2':
            return 'drop table %s cascade;' % self.connection.ops.quote_name(tablename)
        elif engine == 'django.contrib.gis.db.backends.postgis':
            return 'drop table %s cascade;' % self.connection.ops.quote_name(tablename)
        elif engine in ['django.db.backends.sqlite3', 'sqlite3']:
            return 'drop table %s ' % self.connection.ops.quote_name(tablename)
        elif engine in [ 'django.db.backends.oracle', 'oracle']:
            return 'drop table %s cascade constraints;' % self.connection.ops.quote_name(tablename)        
        else:
            raise Exception('Engine "%s" not supportted. Try --destroy option.' % engine)
    
    def handle(self, *args, **options):
        interactive = options.get('interactive', True)
        verbosity = int(options.get('verbosity', 0))
        dropdb = options.get('destroy')
        
        # django 1.3 stealth option -- 'load_initial_data' is used by the testing setup
        # process to disable initial fixture loading.
        load_initial_data = options.get('load_initial_data', True)
        
        self.dbname = options.get('database', DEFAULT_DB_ALIAS)

        if interactive==True:
            confirm = raw_input("""You have requested a flush of the database.
This will IRREVERSIBLY DESTROY all data currently in the %r database,
and return each table to the state it was in after syncdb.
Are you sure you want to do this?

    Type 'yes' to continue, or 'no' to cancel: """ % settings.DATABASES[self.dbname]['NAME'])
        else:
            confirm = 'yes'
            
        if confirm == 'yes':
            self.connection = connections[self.dbname]
            if dropdb:
                self.recreate_db(verbosity )
            else:
                cursor = self.connection.cursor()
                tables = self.connection.introspection.table_names()
                for table in tables:
                    if verbosity > 0:
                        print self.get_drop_table_statement(table)
                    cursor.execute( self.get_drop_table_statement(table) )

            # only django 1.3 has load_initial_data stealth options
            # we need it so we copied as xsyncdb.
            # WILL BE REMOVED IN THE FUTURE 
            call_command('syncdb13', verbosity=verbosity, interactive=interactive, database=self.dbname, load_initial_data=load_initial_data)
            
            
            