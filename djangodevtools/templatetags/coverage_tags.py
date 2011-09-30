# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django import template

register = template.Library()

def module_crumbs(moduleName):
    "Return breadcrumb trail leading to URL for this page"
    pkgs = moduleName.split('.')    
    ret = ""
    name = []
    for item in pkgs[:-1]:
        name.append( item )
        a = ".".join(name)
        ret += '<a href="%s.html">%s</a>.' % (a, item) 

    ret += pkgs[-1]
    return ret

register.simple_tag(module_crumbs)
