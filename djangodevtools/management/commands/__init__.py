import os
from fnmatch import fnmatch
import re

def color_style():
    """Returns a Style object with the Django color scheme."""
    from django.core.management.color import supports_color
    from django.utils import termcolors
    if not supports_color():        
        return no_style()
    class dummy: 
        pass
    style = dummy()
    style.ERROR = termcolors.make_style(fg='red', opts=('bold',))
    style.ERROR_OUTPUT = termcolors.make_style(fg='red', opts=('bold',))
    style.NOTICE = termcolors.make_style(fg='red')
    style.NORMAL = termcolors.make_style()
    style.INFO = termcolors.make_style(fg='white', opts=('bold',))
    style.OK = termcolors.make_style(fg='yellow', opts=('bold',))
    return style

def no_style():
    """Returns a Style object that has no colors."""
    class dummy:
        def __getitem__(self, attr):
            return lambda x: x
        def __getattr__(self, attr):
            return lambda x: x        
    return dummy()

class RegExpList(list):

    def __init__(self, args=[]):
        list.__init__(self)        
        self.mode = 'match'
        for el in args:            
            self.append(el)
    
    def extend(self, itm):
        for el in itm:
            self.append(el)
            
    def append(self, itm):
        if isinstance(itm, basestring):
            list.append(self, re.compile(itm))
        else:
            list.append(self,   itm)
            
    def __contains__(self, value):
        for rule in self:
            if rule.match(str(value)): 
                return True        
        return False
    
    
    
class DevCommand(object):
    exclude = ['.svn,','CVS']
    filenames = ['*.py']
    write = color_style()
    
    def excluded(self, filename):
        """
        Check if options.exclude contains a pattern that matches filename.
        """
        basename = os.path.basename(filename)
        for pattern in self.exclude:
            if fnmatch(basename, pattern):
                return True
    
    
    def filename_match(self, filename):
        """
        Check if options.filename contains a pattern that matches filename.
        If options.filename is unspecified, this always returns True.
        """
        if self.excluded(filename):
            return False
        if not self.filenames:
            return True
        for pattern in self.filenames:
            if fnmatch(filename, pattern):
                return True
    
    def get_all_files_of_app(self, app_info):
        """ app must be a tuple (app_name, target_dir, app) as from get_apps"""
        dirname = app_info[1].rstrip('/')
        ret = []
        if self.excluded(dirname):
            return
        for root, dirs, files in os.walk(dirname):
            dirs.sort()
            for subdir in dirs:
                if self.excluded(subdir):
                    dirs.remove(subdir)
            files.sort()
            for filename in files:
                fqn = os.path.join(root, filename)
                if self.filename_match(fqn):
                    ret.append( fqn )
        return ret
    
    def get_apps(self, *test_labels):
        from django.db.models import get_app, get_apps
        ret = []
        if test_labels:
            apps = [ get_app(a) for a in test_labels]       
        else:
            apps = get_apps()
        for app in apps:
            app_name = ".".join( app.__name__.split(".")[:-1] )
            delta = (".", "..")[(os.path.basename(app.__file__))[:11] == "__init__.py"]      
            target_dir = os.path.abspath(os.path.join(os.path.dirname(app.__file__), delta))                                             
            ret.append((app_name, target_dir, app) )
        return ret
    
#    def reload_applications(self):
#        from django.db.models.loading import AppCache
#        from django.conf import settings
#        cache = AppCache()
#
#        apps_module_names = [app.__name__ for app in cache.get_apps()]
#        apps_module_names += getattr(settings, "RELOAD_ADDITIONAL_MODULES", []) 
#        for x in sys.modules:
#            """
#            To reload the submodules like app/models/office.py
#            check take the left part
#            """
#            if "coverage" in x:
#                continue
#            if "management" in x:
#                continue
#            parts = x.rsplit(".", 1)
#            #print x, [app.__name__ for app in cache.get_apps()]
#            if sys.modules[x]:
#                if x in apps_module_names or parts[0] in apps_module_names:
#                    __import__(sys.modules[x].__name__)
#                    reload(sys.modules[x])
