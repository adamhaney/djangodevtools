#from django.core.management.base import BaseCommand
import datetime
from glob import glob
from django.template.context import Context
from django.template.loader import get_template
from djangodevtools.management.cc import measure_complexity, PrettyPrinter
from optparse import make_option
import os
import sys
import djangodevtools
from djangodevtools.templatetags.cc_tags import app_module_name

GLOBAL_CC = "all"

def find_module(fqn):
    """
    Return function path
    """
    join = os.path.join
    exists = os.path.exists
    partial_path = fqn.replace('.', os.path.sep)
    for p in sys.path:
        path = join(p, partial_path, '__init__.py')
        if exists(path):
            return path
        path = join(p, partial_path + '.py')
        if exists(path):
            return path
    raise Exception('invalid module')
        
from django.core.management.commands import test        
class Command(test.Command, djangodevtools.management.commands.DevCommand): #@UndefinedVariable
    #Create the option list to facilitate developers
    option_list = test.Command.option_list + (   
          make_option('--output','-o', action='store', dest='output', default='console',
                      type='choice', choices=['console', 'json', 'xml', 'html'],
                      help='Output mode; console, json, xml'),
          make_option('--dest', action='store', metavar="DIR", dest='dest_dir', default="cc_dir",
                      help='destination directory of html files'),
    )
    help = """Runs the cyclomatic complexity analysis for specified applications.
For example:
    ./manage.py cc myapp
    """
 
    def add_dir(self, dirname):
        """
        Check all Python source files in this directory and all subdirectories.
        """
        dirname = dirname.rstrip('/')
        if self.excluded(dirname):
            return
        for root, dirs, files in os.walk(dirname):
            dirs.sort()
            for subdir in dirs:
                if self.excluded(subdir):
                    dirs.remove(subdir)
            files.sort()
            for filename in files:
                self.add_file( os.path.join(root, filename) )
     
    def handle(self, *app_labels, **options):
        report_dict = {}
        items = set()
        for arg in app_labels:
            app_set = set()
            if os.path.isdir(arg):
                for f in glob(os.path.join(arg, '*.py')):
                    if os.path.isfile(f):
                        #items.add(os.path.abspath(f))
                        app_set.add(os.path.abspath(f))
            elif os.path.isfile(arg):
                #items.add(os.path.abspath(arg))
                app_set.add(os.path.abspath(arg))
            else:
                # this should be a package'
                app_set.add(find_module(arg))
                #items.add(find_module(arg))
            items = items | app_set
            report_dict[arg] = app_set

        out = options.get("output")

        if out=='json':
            generateJsonOutput(items)
        elif out=='xml':
            generateXmlOutput(items)
        elif out=='html':
            generateHtmlOutput(items, report_dict, *app_labels, **options)
        else:
            generateConsoleOutput(items)

#        appData = {}
#        out = options.get("output")
#        for name, dir, app in self.get_apps( *app_labels ):
#            lista = []
#            for item in self.get_all_files_of_app( (name, dir, app) ):
#                try:
#                    code = open(item).read().rstrip()
#                    stats = measure_complexity(code, item)
#                    fname, classes, functions, complexity = stats
#
#                    fname = fname[len(dir):].replace(os.path.sep, ".")[1:]
#                    lista.append([fname,complexity])
#                except IndentationError, ex:
#                    print self.write.ERROR( " ".join([item, ex.__class__.__name__, str(ex.lineno), ex.msg, ex.text[:-1]]) )
#                except SyntaxError, ex:
#                    if ex.text[0] == "#":
#                        pass
#                    else:
#                        print self.write.ERROR( " ".join([item, ex.__class__.__name__, str(ex.lineno), ex.msg, ex.text]) )
#            appData[name]=lista
#        try:
#            if out=='xml':
#                generateXmlOutput(appData)
#            elif out=='json':
#                generateJsonOutput(self,appData)
#            else:
#                generateConsoleOutput(self,appData)
#        except IndentationError, ex:
#            print self.write.ERROR( " ".join([item, ex.__class__.__name__, str(ex.lineno), ex.msg, ex.text[:-1]]) )
#        except SyntaxError, ex:
#            if ex.text[0] == "#":
#                pass
#            else:
#                print self.write.ERROR( " ".join([item, ex.__class__.__name__, str(ex.lineno), ex.msg, ex.text]) )

def __classes_as_dict(classes):
    data = {}
    for c in classes:
        data[c.name] = {
            'complexity' : c.complexity,
            'methods' : __functions_as_dict(c.functions)
        }
    return data

def __functions_as_dict(functions):
    data = {}
    for f in functions:
        data[f.name] = {
            'complexity' : f.complexity,
        }
    return data
           
def generateConsoleOutput(reportData):
    """
    Show report data on standard output
    """
    for item in reportData:
        code = open(item).read()
        stats = measure_complexity(code, item)
        pp = PrettyPrinter(sys.stdout, verbose=2)
        pp.pprint(item, stats)

def __setup_dest_directory(options, app_labels):
    """
    Creates the cyclomatic complexity directory
    """
    from django.conf import settings
    dest = options.pop('dest_dir', getattr(settings,"CC_DIR", os.path.join(os.path.pardir, "cc_dir" )) )
    output_dir = os.path.abspath( dest )
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if not os.path.exists(output_dir+"/"+GLOBAL_CC):
        os.makedirs(output_dir+"/"+GLOBAL_CC)
    for app_label in app_labels:
        if not os.path.exists(output_dir+"/"+app_label):
            os.makedirs(output_dir+"/"+app_label)
    print "Save cyclomatic complexity data in:" , output_dir
    return output_dir

def __create_header_file(app_labels, options, output_dir, app_name):
    t = get_template('cc_header.tpl.html')
    ctx = Context({
          'app_name': app_name,
          'now': datetime.datetime.now(),
          'cmdline_args': app_labels,
          'cmdline_kwargs': options,
    })
    html = t.render(ctx)
    f = open(output_dir + "/" + app_name + "/header.html", "w")
    f.write(html)
    f.close()

def __create_modules_list_file(output_dir, reportData, app_name):
    t = get_template('cc_modules.tpl.html')
    ctx = Context({
        'app_name': app_name,
        'app': app_name,
        'modules': reportData,
    })
    html = t.render(ctx)
    f = open(output_dir + "/" + app_name + "/modules.html", "w")
    f.write(html)
    f.close()

def __create_summary_file(output_dir, reportData, app_name):
    data = {}
    for item in reportData:
        code = open(item).read()
        stats = measure_complexity(code, item)
        data[item]={
            'complexity' : stats.complexity,
            'functions' : __functions_as_dict(stats.functions),
            'classes' : __classes_as_dict(stats.classes),
        }
    t = get_template('cc_application.tpl.html')
    ctx = Context({
        'reportData': data,
        'app': app_name,
    })
    html = t.render(ctx)
    f = open(output_dir + "/"+app_name+"/summary.html","w")
    f.write(html)
    f.close()
    return data

def __create_index_file(data, output_dir):
    t = get_template('cc_index.tpl.html')
    ctx = Context({
        'reportData': data,
        'GLOBAL_CC': GLOBAL_CC,
    })
    html = t.render(ctx)
    f = open(output_dir + "/index.html", "w")
    f.write(html)
    f.close()

def __create_applications_list_file(app_labels, output_dir):
    apps = []
    apps.append(GLOBAL_CC)
    apps.extend(list(app_labels))
    t = get_template('cc_apps.tpl.html')
    ctx = Context({
        'apps': apps
    })
    html = t.render(ctx)
    f = open(output_dir + "/apps.html", "w")
    f.write(html)
    f.close()

def __create_module_file(output_dir, reportData, app_name):
    data = {}
    for item in reportData:
        code = open(item).read()
        stats = measure_complexity(code, item)
        data[item]={
            'complexity' : stats.complexity,
            'functions' : __functions_as_dict(stats.functions),
            'classes' : __classes_as_dict(stats.classes),
        }
    for k,v in data.iteritems():
        t = get_template('cc_module.tpl.html')
        ctx = Context({
            'app_name': app_name,
            'now': datetime.datetime.now(),
            'sourceFile': k,
            'reportData': data[k]
        })
        html = t.render(ctx)
        filename = app_module_name(k)
        f = open(output_dir + "/"+app_name+"/"+filename+".html","w")
        f.write(html)
        f.close()

def generateHtmlOutput(reportData, report_dict, *app_labels, **options):
    """
    Create a file named reportCc.html containing cyclomatic complexity analysis
    """
    output_dir = __setup_dest_directory(options, app_labels)

    # creates common header page
    __create_header_file(app_labels, options, output_dir, GLOBAL_CC)

    # creates common applications list page
    __create_applications_list_file(app_labels, output_dir)

    # creates common modules list page
    __create_modules_list_file(output_dir, reportData, GLOBAL_CC)

    # creates common summary page
    data = __create_summary_file(output_dir, reportData, GLOBAL_CC)

    # creates common index page
    __create_index_file(data, output_dir)

    for app in app_labels:
        __create_header_file(app_labels, options, output_dir, app)
        __create_modules_list_file(output_dir, report_dict[app], app)
        __create_summary_file(output_dir, report_dict[app], app)
        __create_module_file(output_dir, report_dict[app], app)


def generateXmlOutput(reportMessages):
    """
    Create a file named reportCc.xml containing cyclomatic complexity analysis
    """
    t = get_template('cc_app.tpl.html')
    ctx = Context({
        'reportMessages': reportMessages
    })
    xml = t.render(ctx)
    f = open("reportCc.xml","w")
    f.write( xml )
    f.close()

def generateJsonOutput(reportData):
    """
    Show a json formatted stream containing cyclomatic complexity analysis
    """
    data = {}
    for item in reportData:
        code = open(item).read()
        stats = measure_complexity(code, item)
        data[item]={
            'complexity' : stats.complexity,
            'functions' : __functions_as_dict(stats.functions),
            'classes' : __classes_as_dict(stats.classes),
        }
    from django.utils import simplejson
    json_str = simplejson.dumps(data)
    print json_str
