import json
import os

from fabric.api import *
from fabric.contrib import files, project

P = {'http_demo1': '123'}

env.hosts = ['ktech@www.os4d.org']

#env.pypi_user = secret['username']
#env.pypi_password = secret['password']


def package():
    local('rm -f dist/*')
    local('./setup.py sdist -d dist/')
    put('dist/*', '/data/trac/pypi/djangodevtools')

    local('rm -f dist/*')
    local('./setup.py bdist_egg -d dist/')
    put('dist/*', '/data/trac/pypi/djangodevtools')
