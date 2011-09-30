# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.commands.dumpdata import Command as DumpData
from django.core import serializers
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.utils.datastructures import SortedDict
from django.core.exceptions import ImproperlyConfigured
from django.db.models.fields.related import ForeignKey, ManyToManyField
import sys

def override_option_list(optlist, name, override):
    opt = [el for el in optlist if el._long_opts != [name]]
    opt.append ( override )
    return tuple(opt)

def update_option_list(optlist, name, **kwargs):
    opt = [el for el in optlist if el._long_opts == [name]][0]
    for k,v in kwargs.items():
        setattr(opt, k, v)
    return optlist


class Command(DumpData):
    #option_list = update_option_list(DumpData.option_list, '--indent', default=3)
    option_list = BaseCommand.option_list + (
        make_option('--limit', default=None, dest='limit',
            help='Limit the number of starting instances for each model'),
        make_option('--format', default='json', dest='format',
            help='Specifies the output serialization format for fixtures.'),
        make_option('--indent', default=3, dest='indent', type='int',
            help='Specifies the indent level to use when pretty-printing output'),
        make_option('-e', '--exclude', dest='exclude',action='append', default=[],
            help='App to exclude (use multiple --exclude to exclude multiple apps).'),
        make_option('-i', '--ignore', dest='ignore',action='append', default=[],
            help='app.model to exclude (use multiple --ignore to exclude multiple models ).'),
    )
    
    
    def handle(self, *app_labels, **options):
        from django.db.models import get_app, get_apps, get_models, get_model

        format = options.get('format','json')
        verbosity = options.get('verbosity', 0)
        indent = options.get('indent',3)
        exclude = options.get('exclude',[])
        ignore = options.get('ignore',[])
        limit = options.get('limit', None)
        show_traceback = options.get('traceback', False)

        excluded_apps = [get_app(app_label) for app_label in exclude]

        if len(app_labels) == 0:
            app_list = SortedDict([(app, None) for app in get_apps() if app not in excluded_apps])
        else:
            app_list = SortedDict()
            for label in app_labels:
                try:
                    app_label, model_label = label.split('.')                    
                        
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError("Unknown application: %s" % app_label)

                    
                    model = get_model(app_label, model_label)
                    
                    if model is None:
                        raise CommandError("Unknown model: %s.%s" % (app_label, model_label))

                    if app in app_list.keys():
                        if app_list[app] and model not in app_list[app]:
                            app_list[app].append(model)
                    else:
                        app_list[app] = [model]
                except ValueError:
                    # This is just an app - no model qualifier
                    app_label = label
                    try:
                        app = get_app(app_label)
                    except ImproperlyConfigured:
                        raise CommandError("Unknown application: %s" % app_label)
                    app_list[app] = None

        # Check that the serialization format exists; this is a shortcut to
        # avoid collating all the objects and _then_ failing.
        if format not in serializers.get_public_serializer_formats():
            raise CommandError("Unknown serialization format: %s" % format)

        try:
            serializers.get_serializer(format)
        except KeyError:
            raise CommandError("Unknown serialization format: %s" % format)

        objects = []
        for app, model_list in app_list.items():
            if model_list is None:
                model_list = get_models(app)

            for model in model_list:
                if model.__name__ in ignore:
                    continue
                if not model._meta.proxy:
                    try:
                        if limit:
                            objects.extend(model._default_manager.all()[:limit])
                        else:
                            objects.extend( model._default_manager.all() )
                    except Exception, e:
                        print e
                        pass

        def log(msg, obj):
            sys.stderr.write('%s %25s: %25s (%s)\n' % (msg, obj.__class__.__name__, obj, obj.pk )) 
            
        def inspect( obj, cache):
            if not obj:
                return cache

            if not obj in cache:
                if verbosity > 0:
                    log(self.style.SQL_FIELD('Adding...'), obj)
                cache.add( obj )
            else:
                log(self.style.SQL_KEYWORD('Ignoring.'), obj)            
            
            for f in itertools.chain(obj._meta.fields, obj._meta.many_to_many):
                if issubclass(f.__class__, ForeignKey):
                    inspect( getattr(obj, f.name), cache )   
                elif issubclass(f.__class__, ManyToManyField):
                    mm = getattr(obj, f.name)
                    for m in mm.all():
                        inspect( m, cache )   

        if limit:
            for o in objects:
                log(self.style.SQL_FIELD('Present..'), o)
                    
            c = set(objects)
            import itertools
            
            for m in objects:
                inspect(m, c)
            
            objects = c

        try:
            return serializers.serialize(format, objects, indent=indent)
        except Exception, e:
            if show_traceback:
                raise
            raise CommandError("Unable to serialize database: %s" % e)
