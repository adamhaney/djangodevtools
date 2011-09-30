# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

original code by mpasternacki  http://djangosnippets.org/snippets/1762/

'''

from django.core.management.base import BaseCommand, make_option
import compiler
import sys

import pyflakes.checker
from djangodevtools.management.commands import DevCommand, RegExpList

def check(codeString, filename):
    """
    Check the Python source given by C{codeString} for flakes.

    @param codeString: The Python source to check.
    @type codeString: C{str}

    @param filename: The name of the file the source came from, used to report
        errors.
    @type filename: C{str}

    @return: The number of warnings emitted.
    @rtype: C{int}
    """
    # Since compiler.parse does not reliably report syntax errors, use the
    # built in compiler first to detect those.
    try:
        try:
            compile(codeString, filename, "exec")
        except MemoryError:
            # Python 2.4 will raise MemoryError if the source can't be
            # decoded.
            if sys.version_info[:2] == (2, 4):
                raise SyntaxError(None)
            raise
    except (SyntaxError, IndentationError), value:
        msg = value.args[0]

        (lineno, offset, text) = value.lineno, value.offset, value.text

        # If there's an encoding problem with the file, the text is None.
        if text is None:
            # Avoid using msg, since for the only known case, it contains a
            # bogus message that claims the encoding the file declared was
            # unknown.
            return ["%s: problem decoding source" % (filename, )]
        else:
            line = text.splitlines()[-1]

            if offset is not None:
                offset = offset - (len(text) - len(line))

            return ['%s:%d: %s' % (filename, lineno, msg)]
    else:
        # Okay, it's syntactically valid.  Now parse it into an ast and check
        # it.
        tree = compiler.parse(codeString)
        w = pyflakes.checker.Checker(tree, filename)

        lines = codeString.split('\n')
        messages = [message for message in w.messages
                    if lines[message.lineno-1].find('pyflakes:ignore') < 0]
        messages.sort(lambda a, b: cmp(a.lineno, b.lineno))

        return messages


def checkPath(filename):
    """
    Check the given path, printing out any warnings detected.

    @return: the number of warnings printed
    """
    try:
        return check(file(filename, 'U').read() + '\n', filename)
    except IOError, msg:
        return ["%s: %s" % (filename, msg.args[1])]


class Command(BaseCommand, DevCommand):
    option_list = BaseCommand.option_list + (
            make_option('-i', '--ignore', action='append', metavar="REGEX", dest='ignore', default=[],
            help='ignore REGEX matching errors'),
            )
    
    help = "Run pyflakes syntax checks."
    args = '[app [app [...]]]'
    can_import_settings = False
    requires_model_validation = False

    def handle(self, *app_labels, **options):        
        ignore = RegExpList( options['ignore'] )
        warnings = []
        for name, dir, app in self.get_apps( *app_labels ):
            for filepath in self.get_all_files_of_app( (name, dir, app) ):
                warnings.extend( checkPath(filepath) )
        
        warnings = filter( lambda x:x not in ignore, warnings)
        for warning in warnings:
            print warning        
        
        if warnings:
            print 'Total warnings: %d' % len(warnings)
            raise SystemExit(1)
