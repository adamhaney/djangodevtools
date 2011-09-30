# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''

from coverage import coverage
import djangodevtools

from django.core.management.base import BaseCommand, make_option
from djangodevtools.management.cover import CoverageTool
import sys
#from django.utils import importlib
import os

class Command(BaseCommand, djangodevtools.management.commands.DevCommand): #@UndefinedVariable
    '''
    Note:
    to allow manage.py to handle aliases directly as extra commands
    put following lines in your settings.py :

        from djangodevtools import manage_enable_coverage
        manage_enable_coverage()
    '''
    option_list = BaseCommand.option_list + (
        make_option('--dest', action='store', metavar="DIR", dest='dest_dir', default="coverage_dir",
            help='destination directory of html files'),
        make_option('--report', action='store', type="choice", dest='report', default='html', 
                    choices=['html', 'classic','raw','xml'], help='Use the coverage html original report'),

#        make_option('--classic-report', action='store_true', metavar="BOOLEAN", dest='old_report', default=False,
#            help='Use the coverage html original report'),
#        make_option('--report', action='store_true', metavar="BOOLEAN", dest='old_report', default=False,
#            help='Use the coverage html original report'),
    )
    help = """Runs the coverage for sub subcommand.
Example:
    ./manage.py cover test myapp
    """
    args = '<subcommand>'
    can_import_settings = False
    requires_model_validation = False

    def load_all_modules_of_apps(self, *app_names):
        ''' Takes modules from applications'''
        apps = self.get_apps(*app_names)        
        for app in apps:
            if self.verbosity >=3:
                print "Processing app %s" %  app[0]
            if not app[0].startswith('django.'):
                for f in  self.get_all_files_of_app(app):
#                    if self.verbosity >=3:
#                        print "  Found module %s" %  f
                    if not '__init__' in f:
                        mod = app[0] + f[ len(app[1]):].replace(os.path.sep,'.').replace('.py','')
                    else:
                        mod = app[0] + f[ len(app[1]):].replace(os.path.sep,'.').replace('.__init__.py','')
                    
                    if self.verbosity >=3:
                        print "  Importing %s" %  mod
                    
                    m = __import__(mod)
                    try:
                        #try to reload the module. Could be loaded before 
                        reload( m )
                    except:
                        print "   Error Reloading %s" % mod
                        
    def handle(self, cmd=None, *args, **options):
        if not cmd:
            self.print_help(None, "cover")
            return
        self.verbosity = int(options.get('verbosity',1))
        tool = CoverageTool()
        tool.cmdline_args =  sys.argv[0:2] + list(args)
        tool.cmdline_kwargs = options
        
        tool._setup_dest_directory( options )
        tool.report = options.pop('report', False)

        from django.conf import settings
        tool.mod_enabled =  getattr(settings,"COVERAGE_MODULES",  getattr(settings,"INSTALLED_APPS") )
        cov = coverage(source=tool.mod_enabled)        
        cov.erase()
        cov.use_cache(0)
        cov.start()
        
        self.load_all_modules_of_apps( *tool.mod_enabled )
        try:
            from django.core.management import call_command
            call_command(cmd, *args, **options)
        finally:
            cov.stop()
    
            if tool.report == 'html':
                tool.html_report(cov)
            elif tool.report == 'classic':
                cov.html_report(directory=tool.output_dir)
            elif tool.report == 'xml':
                cov.xml_report(directory=tool.output_dir)
            else:
                print cov.analysis2
            
