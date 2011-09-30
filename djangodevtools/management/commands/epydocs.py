# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from epydoc import cli
from django.conf import settings
import os
from djangodevtools.management.commands import DevCommand

class Options(object):
    simple_term = False
    debug = True
    action = 'html' # ('html', 'text', 'latex', 'dvi', 'ps', 'pdf', 'check')
    docformat = 'plaintext'#('epytext', 'plaintext', 'restructuredtext', 'javadoc')
    inheritance="grouped" #  ('grouped', 'listed', 'included')
    css = 'white'  # ['blue', 'default', 'grayscale', 'black', 'green', 'white']
    target = '/home/sax/Desktop/epy'
    verbosity = 0
    include_log = False
    dotpath = '/usr/bin/dot'  # path to Graphviz dot  
    graph_font = 'helvetica'
    graph_font_size= 14 
    graphs=('classtree', 'callgraph', 'umlclasstree') #('classtree', 'callgraph', 'umlclasstree')   

    show_frames=True
    show_private=True
    show_imports=True
    verbose=0
    quiet=0
    load_pickle=False
    parse=True
    introspect=False # --parse-only
    profile=False
    list_classes_separately=True
    include_source_code=True
    pstat_files=[]
    simple_term=False
    fail_on=None    
    exclude=[]
    exclude_parse=[]
    exclude_introspect=[]    
    external_api=[]
    external_api_file=[]
    external_api_root=[]
    redundant_details=False
    src_code_tab_width=8
    def repr(self):
        return 
    
class Command(BaseCommand, DevCommand):
    #Create the option list to facilitate developers
    option_list = BaseCommand.option_list + (
    make_option('--action', action='store', dest='action', default='html',
                type='choice', choices=cli.ACTIONS,
                help='output type [html|text|latex|dvi|ps|pdf|check]'),

    make_option('--debug', action='store_true', dest='debug'),

    make_option('--css', action='store', dest='css', default='white',
                type='choice', choices=cli.CSS_STYLESHEETS.keys(),
                help='css [blue|default|grayscale|black|green|white]'),

    make_option('--graph', action='append', dest='graphs', metavar='GRAPHTYPE',
                type='choice', choices=cli.GRAPH_TYPES,
                help=("Include graphs of type GRAPHTYPE in the generated output.  "
                      "Graphs are generated using the Graphviz dot executable.  "
                      "If this executable is not on the path, then use --dotpath "
                      "to specify its location.  This option may be repeated to "
                      "include multiple graph types in the output.  GRAPHTYPE "
                      "should be one of: [all|%s]" % '|'.join(cli.GRAPH_TYPES))),

    make_option("--docformat", dest="docformat", metavar="NAME", default=cli.DEFAULT_DOCFORMAT,
                help="The default markup language for docstrings.  Defaults "
                     "to \"%s\"." % cli.DEFAULT_DOCFORMAT),

    make_option('--target', action='store', dest='target', default='./apidoc',
                help="The output directory.  If PATH does not exist, then "
                     "it will be created."),

    make_option('--all-applications', '-a', action='store_true', dest='all_applications',
                help='Automaticly include all applications from INSTALLED_APPS'),

    )

    def handle(self, *app_labels, **options):
        if len(app_labels) < 1 and not options['all_applications']:
            raise CommandError("need one or more arguments for appname")

        if options.get('all_applications', False):
            app_labels = settings.INSTALLED_APPS

        opt = Options()
        for v in ('action', 'css','graphs','docformat', 'target', 'debug'):
            setattr(opt, v, options.get(v))
        print opt


        # cli function config file and run the documentation build
        #for app_name, target_dir, app in self.get_apps(*app_labels):
        #    os.chdir(target_dir)
        os.chdir('pasport')
        cli.main(opt, ['models'])
        #    cli.main(opt, [app_name])
