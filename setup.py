#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''

from setuptools import setup
import os
import sys

APPLICATION = 'djangodevtools'

def fullsplit(path, result = None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def scan_dir(target):
    packages, data_files = [], []
    for dirpath, dirnames, filenames in os.walk(target):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])
    return packages, data_files

packages, data_files = scan_dir('djangodevtools')
#data_files.append(['djangodevtools/management', ['djangodevtools/management/compiler.jar']])

# Small hack for working with bdist_wininst.
# See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
    for file_info in data_files:
        file_info[0] = '\\PURELIB\\%s' % file_info[0]

version = __import__(APPLICATION).get_version()
if u'dev' in version:
    version = '%sdev-r%s' % (version.split(' ')[0], version.split(' ')[2])
elif u'final' in version:
    version = '%s-r%s' % (version.split(' ')[0], version.split(' ')[2])

try:
    import os4d.setuptools.upload
    cmdclasses = {"upload": os4d.setuptools.upload.Upload}
except ImportError:
    cmdclasses = {}

setup(
    name = APPLICATION,
    version = version,
    url = 'http://www.os4d.org/pypi/%s' % APPLICATION,
    author = 'Ktech.s.r.l.',
    author_email = 'k-tech@k-tech.it',
    license = "MIT License",
    description = 'Django Development Tools',
    download_url = 'http://os4d.org/pypi/%s/%s-%s.tar.gz' % (APPLICATION, APPLICATION, version),
    packages = packages,
    data_files = data_files,
    platforms = ['any'],
    zip_safe = False,
    test_suite =  "djangodevtools.runtests.runtests",
    cmdclass = cmdclasses,
    extras_require = {'dev':['os4d']},
    install_requires = [
        'distribute',
        'coverage>=3.4',
        'pygments>=1.3.1',
        'pyflakes==0.4.0',
        'epydoc>=3.0.1',
        'ipython',
        'configobj>=4.7.2',
        'pep8',
        'cherrypy>=3.1.2',
    ],
    dependency_links = [ 'http://www.os4d.org/pypi', ],
    classifiers = ['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP',
                   'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
                   'Topic :: Internet :: WWW/HTTP :: WSGI',
                   'Topic :: Software Development :: Libraries :: Application Frameworks',
                   'Topic :: Software Development :: Libraries :: Python Modules',
                   ],
    long_description = \
"""
Welcome to the Django Development Tools Project
Djangodevtools is a pluggable django application that provides for a set of  custom management commands.

You can easly setup your django project for using it. The purpose is to help the software development process and to compliance checking with recognized standards, to build the documentation and more.

For this wiki, we are taking a free inspiration by  djangoproject.
""",

)
