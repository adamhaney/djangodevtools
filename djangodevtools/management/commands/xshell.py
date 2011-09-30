# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import NoArgsCommand, make_option

        
class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
#        make_option('--autocall', dest='autocall', default=1,
#            help='automatically call any callable object'),
                
        make_option('--deep_reload', action='store_true', dest='deep_reload',
            help='enable deep auto reload'),

        make_option('--pprint', action='store_true', dest='pprint',
            help='enable deep auto reload'),
    
    )
    help = "Ipython shell interface in which all models are loaded (no need to import them)"

    requires_model_validation = True

    def collect_packages(self):
        from django.db.models.loading import get_models, get_apps            
        self.all_models = {}
        for app_mod in get_apps():
            app_models = get_models(app_mod)
            if not app_models:
                continue
            model_labels = ", ".join([model.__name__ for model in app_models])
            print self.style.SQL_COLTYPE("From '%s' autoload: %s" % (app_mod.__name__.split('.')[-2], model_labels))
            for model in app_models:
                try:
                    self.all_models[model.__name__] = getattr(__import__(app_mod.__name__, {}, {}, model.__name__), model.__name__)
                except AttributeError, e:
                    print self.style.ERROR_OUTPUT("Failed to import '%s' from '%s' reason: %s" % (model.__name__, app_mod.__name__.split('.')[-2], str(e)))
                    continue
                
    def handle_noargs(self, **options):
        from djangodevtools.management.xshell_macro import __extensions__
        #from django.db.models.loading import get_models, get_apps        
        #loaded_models = get_models()
        
        ipython_args = ['-automagic','-nobanner', '-autocall', '2']
        
        #autocall = not options.get('autocall', '1')
        #deep_reload = not options.get('deep_reload', False)
        #pprint = not options.get('pprint', False)
        
        for opt in ('pprint', 'deep_reload'):
            if options.get(opt, False):
                ipython_args.append( '-%s' % opt )                   
            else:
                ipython_args.append( '-no%s' % opt )
        
        for opt in ('autocall',):
            value = options.get(opt, None) 
            if value != None:
                ipython_args.append( ('-%s' % opt, value) )

        self.collect_packages()
           
        try:
            import IPython
            from IPython import ipapi

            argv = ipython_args
            shell = IPython.Shell.IPShell(argv=argv, user_ns=self.all_models)
            ip = ipapi.IPApi(shell.IP)
            
            for k,v in __extensions__.items():
                ip.expose_magic(k, v )

            shell.mainloop()
        except ImportError:
            raise
