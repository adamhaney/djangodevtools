# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand, make_option
from django.template.context import Context
from django.template.loader import get_template
#from djangodevtools.externals import pep8 
from djangodevtools.management.commands import DevCommand
import re
import sys
import pep8

default_exclude = '.svn,CVS,*.pyc,*.pyo,INSTALL'
default_include = '*.py'

class Command(BaseCommand, DevCommand):
    #Create the option list to facilitate developers
    option_list = BaseCommand.option_list +(
               make_option('--verbose', default=0, action='count',
                      help="print status messages, or debug with -vv"),                                            
               make_option('--exclude', '-e', action='store', dest='exclude', default=default_exclude,
                     help="skip matches (default %s)" % default_exclude ),
               make_option('--filename', action='store', dest='filename', 
                     help="only check matching files (default %s)" % default_include ),
               make_option('--ignore', metavar='errors', default=None,
                      help="skip errors and warnings (e.g. E4,W)"),
               make_option('--repeat', action='store_true', default=True,
                      help="show all occurrences of the same error" ),
               make_option('--show-source', action='store_true',
                      help="show source code for each error" ),
               make_option('--show-pep8', action='store_true',
                      help="show text of PEP 8 for each error" ),
               make_option('--statistics', action='store_true',
                      help="count errors and warnings" ),
               make_option('--benchmark', action='store_true',
                      help="measure processing speed" ),
               make_option('--output','-o', action='store', dest='output', default='console',
                           type='choice', choices=['console', 'json', 'xml'], 
                           help='Output mode; console, json, xml'),
               
    )
    
    help = 'Runs the test suite for the specified applications, or the entire site if no apps are specified.'
    args = '[appname ...]'
    label = 'application name'
    
    requires_model_validation = False
    
    def generateJsonOutput(self,reportMessages):
        '''
        This function shows a json formatted stream containing pep8 validation errors on standard output
        '''
        from django.utils import simplejson
        json_str = simplejson.dumps(reportMessages)
        print json_str
        
    def generateXmlOutput(self,reportMessages):
        '''
        This function creates a file named reportPep8.xml containing the report of pep8 validation errors
        '''         
        t = get_template('pep8.tpl.html')
        c = Context({'reportMessages': reportMessages})
        xml = t.render(c)
        fp = open("reportPep8.xml","w")
        fp.write( xml )
        fp.close()

    def generateConsoleOutput(self,applicationsMsg):
        '''
        This function shows all messages on standard output
        '''         
        for messages in applicationsMsg:
            print messages
    
    def handle(self, *test_labels, **opts):
        reportMessages = {}
        appMessages = []
        
        def writer(name):
            reportMessages[name] = []
            rex = re.compile(r"^/(?P<filename>.*):(?P<row>\d{1,}):(?P<col>\d{1,}): (?P<code>[A-Z]\d\d\d) (?P<msg>.*)$")
            def storeMessage( msg ):
                appMessages.append(msg)
                m = rex.match( msg )
                if m:
                    reportMessages[name].append( m.groups() )
            return storeMessage
        
        pep8_options =  ['','--filename','*.py']
        #[ pep8_options.extend(['--ignore', x]) for x in opts.get('ignore','').split(',') ]
        if opts.get('ignore', False):
            pep8_options.extend(['--ignore', opts['ignore']])
        pep8_options.extend( [ k for k in ['--show-source', '--show-pep8','--verbose' ] if k in sys.argv[1:] ])
        #pep8_options.extend( [ k for k in ['--show-source', '--show-pep8','--verbose' ] if k in opts ])
        pep8.process_options(pep8_options)
        
        for name, dir, app in self.get_apps( *test_labels ): 
            if 'django' == name:
                continue
            pep8.message = writer(name)
            pep8.input_dir( dir )
        
        if opts.get("output")=='json':
            self.generateJsonOutput(reportMessages)
        elif opts.get("output")=='xml':
            self.generateXmlOutput(reportMessages)
        else:
            self.generateConsoleOutput(appMessages)
