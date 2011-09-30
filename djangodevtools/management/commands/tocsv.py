# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import CommandError
from django.core.management.commands.dumpdata import Command as c
from django.utils.datastructures import SortedDict
from django.db import models
import sys
import csv 
import codecs
import cStringIO
from django.core.exceptions import ImproperlyConfigured

class format(csv.Dialect):
    """Describe the usual properties of Excel-generated CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = False
    lineterminator = '\r\n'
    quoting = csv.QUOTE_ALL
csv.register_dialect("format", format)

class UnicodeWriter(csv.DictWriter):
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """
    
    def __init__(self, f, fieldnames, restval="", extrasaction="raise",
                 dialect="excel", encoding="utf-8", *args, **kwds):
        csv.DictWriter.__init__(self, f, fieldnames, restval, extrasaction, dialect, *args, **kwds)
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
    
    def _dict_to_list(self, rowdict):
        ''' Return a list from a dictionary
        '''
        if self.extrasaction == "raise":
            for k in rowdict.keys():
                if k not in self.fieldnames:
                    raise ValueError("dict contains fields not in fieldnames")
        return [rowdict.get(key, self.restval) for key in self.fieldnames]
    
    def writerow(self, row):
        '''Fetch UTF-8 output from the queue, reencode it into the target encoding,
        and write to the target stream'''
        values = self._dict_to_list(row)
        self.writer.writerow([unicode(s).encode("utf-8") for s in values])
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        data = self.encoder.encode(data)
        self.stream.write(data)
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
class Command(c):
       
    def _get_apps(self, *app_labels):  
        '''Return a dictionary - keys are applications and values are applications models'''       
        from django.db.models import get_app, get_apps, get_model
        excluded_apps = []
        
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
            
        return app_list

    def _get_all_models_for_app(self, app_list):
        from django.db.models import get_models
        for app, model_list in app_list.items():
            if model_list is None:
                model_list = get_models(app)
            app_list[app] = model_list
    
    
    def _dump(self, model):
        '''Get data from applications models and write them to CSV file'''
        headers = []
        for f in model._meta.fields:
            if isinstance(f, models.ForeignKey ):
                headers.append( "%s_id" % f.name )
            headers.append( f.name )  
            
        qs = model.objects.all()
#        writer = csv.DictWriter(sys.stdout, headers, dialect="format")
        writer = UnicodeWriter(sys.stdout, headers, dialect="format")
        writer.writerow(dict(zip(headers,headers)))

        for obj in qs:
            try:
                row = {}
                for field in headers:
                    val = getattr(obj, field)
                    if callable(val):
                        val = val()
                    elif isinstance(val, models.Model):
                        val = val
                    row[field] = val
                    
                writer.writerow(row)
            except:
                print obj.pk, obj
                raise
            
            
        
        
    def handle(self, *app_labels, **options):
        #Create the option list to facilitate developers
        options['indent'] = options.get('indent') or 3       
        options['format'] = options.get('format') or 'json'    
        
        app_list = self._get_apps(*app_labels)
        self._get_all_models_for_app(app_list)
                    
        for app, model_list in app_list.items():
            for model in model_list:
                self._dump(model)

