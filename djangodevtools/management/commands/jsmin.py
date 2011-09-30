# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand, CommandError, make_option
from django.conf import settings
import os
from djangodevtools.externals.jsmin import JavascriptMinify

class Command(BaseCommand):
    #Create the option list to facilitate developers
    option_list = BaseCommand.option_list + (        
        make_option('--target', action='store', dest='js_output_file', default= os.path.abspath(os.path.join(settings.MEDIA_ROOT, 
                                                                                                             'jsmin.js')),
            help="The output directory.  If PATH does not exist, then "
            "it will be created."),
            
        make_option('--base', action='store', dest='base', default= settings.MEDIA_ROOT,
            help="home dir of script" ),
    )
    
    def handle(self, *scripts, **options):
        if len(scripts) < 1 :
            raise CommandError("need at least one script name")
        base = options.get('base')
        #Open and read the js file for input  
        for script in scripts:
            inputstream = open(base + "/" + script)
        #Create a js file for output
        outputstream = open(options.get('js_output_file'),'w')
        jsm = JavascriptMinify()
        JavascriptMinify.minify(jsm,inputstream,outputstream)
        print options.get('js_output_file')
        
        
        