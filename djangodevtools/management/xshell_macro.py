# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
    
def interrogate(item):
    """Print useful information about item."""
    if hasattr(item, '__name__'):
        print "NAME:    ", item.__name__
    if hasattr(item, '__class__'):
        print "CLASS:   ", item.__class__.__name__
    print "ID:      ", id(item)
    print "TYPE:    ", type(item)
    print "VALUE:   ", repr(item)
    print "CALLABLE:",
    if callable(item):
        print "Yes"
    else:
        print "No"
    if hasattr(item, '__doc__'):
        doc = getattr(item, '__doc__')
    doc = doc.strip()   # Remove leading/trailing whitespace.
    firstline = doc.split('\n')[0]
    print "DOC:     ", firstline

def get_all():
    from django.db.models.loading import get_models, get_apps
    reload_cmds = {}
    for app_mod in get_apps():
        app_name = ".".join(app_mod.__name__.split(".")[:-1])
        app_models = get_models(app_mod)
        if not app_models:
            continue
        reload_cmds[ app_name ] = []
        #model_labels = ", ".join([model.__name__ for model in app_models])
        for model in app_models:
            try:                
                getattr(__import__(app_mod.__name__, {}, {}, model.__name__), model.__name__)
                module_name = model.__module__
                reload_cmds[ app_name ].append( "import %s; reload(%s); from %s import %s" % ( module_name, module_name, module_name, model.__name__ ) )                
            except AttributeError:
                continue
    return reload_cmds

def curried():
    mods = get_all()
    def reloadmodels(shell, arg ):
        """
        Ricarica tutti i models django caricati all'inizio della sessione
        uso: reloadmodels [appname]
                  
        """
        filter = arg if arg else mods.keys()
        for app, cmds in mods.items():            
            if app in filter:
                for cmd in cmds:
                    print cmd
                    shell.api.ex(cmd)
    return reloadmodels

def reloadCode(shell, arg):
    try:
        obj =  shell.user_global_ns[arg]
        module_name = obj.__module__
        cmd = "import %s; reload(%s); from %s import %s" % ( module_name, module_name, module_name, arg )  
        shell.api.ex(cmd)
    except KeyError:
        print "Cannot find %s" % arg 

def test(shell, arg):
    pass

def create_request(shell, arg):
    return ""
    
def tree_model(shell, arg):
    try:
        obj =  shell.user_global_ns[arg]
        for b in obj.__bases__:
            print b
    except KeyError:
        print "Cannot find %s" % arg 



__extensions__ = {'reloadmodels': curried(),
                  'rl': reloadCode,
                  'tree': tree_model,
                  'test': test
                  }

