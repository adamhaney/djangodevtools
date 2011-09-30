# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand, CommandError, make_option
from django.conf import settings
from subprocess import Popen
import os
import fnmatch
import sys

def findInSubdirectory(pattern, path):
    '''Return a list of js files'''
    ret = []
    for root, dirs, files in os.walk(path):
        dirs.sort()
        for subdir in dirs:
            if subdir.startswith( '.'):
                dirs.remove(subdir)        
        files.sort()
        for filename in files:
            fqn = os.path.abspath(os.path.join(root, filename))
            if fnmatch.fnmatch(filename, pattern):
                ret.append( fqn )
    return ret
    
OPTIMIZATIONS_LEVEL=['WHITESPACE_ONLY', 'SIMPLE_OPTIMIZATIONS', 'ADVANCED_OPTIMIZATIONS']
WARNING_LEVELS =  ['QUIET','DEFAULT','VERBOSE']
      
class Command(BaseCommand):
    option_list = BaseCommand.option_list + (        
        make_option('--target', action='store', dest='js_output_file', 
                    default= os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'closure.js')),
            help="The output directory.  If PATH does not exist, then it will be created."),
            
        make_option('--base', action='store', dest='base', default= settings.MEDIA_ROOT,
            help="home dir of scripts [%s]" % settings.MEDIA_ROOT),

        make_option('--jar', action='store', dest='jar', default=None, help="path of closure.jar"),

        make_option('--compilation_level', action='store', dest='compilation_level', 
                    type='choice',  choices= OPTIMIZATIONS_LEVEL,
                    default= OPTIMIZATIONS_LEVEL[0],
                    help="Specifies the compilation level to use.Options: [%s]" % '|'.join(OPTIMIZATIONS_LEVEL)),

        make_option('--warning_level', action='store', dest='warning_level', 
                    type='choice',  choices= WARNING_LEVELS,
                    default= WARNING_LEVELS[1],
                    help="Specifies the warning level to use.Options: [%s]" % '|'.join(WARNING_LEVELS)),
    )
    
    def handle(self, *scripts, **options):
        if len(scripts) < 1 :
            raise CommandError("need at least one script name")
        if options.get('jar', False):
            closure_jar = options.get('jar')
        else:
            closure_jar = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'compiler.jar'))
        
        if not os.path.exists(closure_jar):
            sys.exit(1)
            
        base = options.get('base')
        founded = []
        for script in scripts:
            founded.extend( findInSubdirectory(script, base) )
    
        #The application core is managed by compiler.jar
        opts = ['java -jar', closure_jar ]
        for cco in ('warning_level', 'compilation_level', 'js_output_file'):
            opts.extend( ( '--%s' % cco, options.get(cco))  )
        
        for s in founded:        
            opts.append( '--js %s' % s)
        cmd =  ' '.join(opts)
        print cmd
        process = Popen(cmd, shell=True)   
        process.wait()
        print options.get('js_output_file')

