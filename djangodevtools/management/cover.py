# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
import os
import sys
import datetime
from pygments import format, lex
from pygments.lexers import get_lexer_by_name
from pygments.formatters.html import HtmlFormatter
import codecs
from djangodevtools.management.commands import RegExpList

GLOBAL_COVERAGE = "all"

class CssHtmlFormatter(HtmlFormatter):

    def __init__(self, **options):
        HtmlFormatter.__init__(self, **options)
        self.hl_lines = {None: self.hl_lines}
        if isinstance(options.get('css_lines'), dict):
            for k, lines in options['css_lines'].items():
                self.hl_lines[k] = set()
                for lineno in lines:
                    try:
                        self.hl_lines[k].add(int(lineno))
                    except ValueError:
                        pass

    def _highlight_lines(self, tokensource):
        """
        Highlighted the lines specified in the `hl_lines` option by
        post-processing the token stream coming from `_format_lines`.
        """
        if not isinstance(self.hl_lines, dict):
            HtmlFormatter._highlight_lines(tokensource)
        else:
            hl_lines = {}
            for css, lines in self.hl_lines.items():
                hl_lines.update(dict([(line, css) for line in lines]))

            hls = hl_lines.keys()
            for i, (t, value) in enumerate(tokensource):
                if t != 1:
                    yield t, value
                if i + 1 in hls: # i + 1 because Python indexes start at 0
                    css = hl_lines[i + 1]
                    if css:
                        yield 1, '<span class="%s">%s</span>' % (css, value)
                    elif self.noclasses:
                        style = ''
                        if self.style.highlight_color is not None:
                            style = (' style="background-color: %s"' %
                                     (self.style.highlight_color,))
                        yield 1, '<span%s>%s</span>' % (style, value)
                    else:
                        yield 1, '<span class="hll">%s</span>' % value
                else:
                    yield 1, value


class AppData():
    def __init__(self, name, label = None):
        self.name = name
        self.label = label or name
        self.total_lines = 0
        self.total_uncovered_lines = 0
        self.total_covered_lines = 0
        self.total_excluded_lines = 0
        self.modules = []

    def update(self, tl, uncovered_lines, excluded_lines, mod):        
        ''' Updates coverage data 
            @param tl                 total lines
            @param uncovered_lines    total uncovered_lines
            @param xcluded_lines      total excluded_lines
            @param mod                module
        '''
        self.total_lines += tl
        self.total_uncovered_lines += uncovered_lines
        self.total_covered_lines += (tl - uncovered_lines)
        self.total_excluded_lines += excluded_lines
        self.modules.append(mod)

    def coverage(self):
        '''Returns the percentage of covered lines'''
        try:
            return self.total_covered_lines * 100. / self.total_lines
        except ZeroDivisionError:
            return 0.

    def __repr__(self):
        return "<AppData %s>" % self.name

class AppDataDict:
    def __init__(self):
        self.data = {}

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def values(self):
        return self.data.values()

    def __setitem__(self, item, value):
        if not item in self.data:
            self.data[item] = AppData(item, value)

    def __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __contains__(self, item):
        return self.data.__contains__(item)

    def __repr__(self):
        return self.data.__repr__()



class CoverageTool(object):
    def write_files(self, ctx):
        ''' Creates the report structure (index, summary, etc)'''
        from django.template.loader import get_template
#        files  = ['coverage_summary',
#                  'coverage_modules',
#                  'coverage_header']

        k = self.summary_data.keys()
        k.sort()
        ctx["apps"] = k
        ctx["datadict"] = self.summary_data

#        dest = os.path.join(self.outputDir)
        t = get_template('coverage_index.tpl.html')
        html = t.render(ctx)
        fp = self.get_file_handle('', "index")
        fp.write(html)
        fp.close()

        t = get_template('coverage_app.tpl.html')
        html = t.render(ctx)
        fp = self.get_file_handle('', "app")
        fp.write(html)
        fp.close()

        for app in k:
            self.summary_data[app].modules.sort()

            ctx["modules"] = self.summary_data[app].modules
            ctx["app_name"] = app
            ctx["co"] = self.summary_data[app].coverage()
            ctx["tl"] = self.summary_data[app].total_lines
            ctx["cl"] = self.summary_data[app].total_covered_lines
            ctx["el"] = self.summary_data[app].total_excluded_lines

            t = get_template('coverage_summary.tpl.html')
            html = t.render(ctx)

            fp = self.get_file_handle(app, "summary")
            fp.write(html)
            fp.close()

            t = get_template('coverage_modules.tpl.html')
            html = t.render(ctx)

            fp = self.get_file_handle(app, "modules")
            fp.write(html)
            fp.close()

            t = get_template('coverage_header.tpl.html')
            html = t.render(ctx)

            fp = self.get_file_handle(app, "header")
            fp.write(html)
            fp.close()

    def write_index(self, total_lines, total_covered_lines, total_excluded_lines):
        ''' Returns context to set reports '''
        from django.template import Context
        now = datetime.datetime.now()

        self.summary_data[GLOBAL_COVERAGE].modules.sort()

        co = total_covered_lines > 0 and float(total_covered_lines * 100 / total_lines) or 0
        ctx = Context({'now': now,
                                 'modules': self.summary_data[ GLOBAL_COVERAGE ].modules,
                                 'tl':total_lines,
                                 'cl': total_covered_lines,
                                 'el': total_excluded_lines,
                                 'co': co,
                                 'cmdline_args': self.cmdline_args,
                                 'cmdline_kwargs': self.cmdline_kwargs,
                                 'title': "Coverage",
                                 'GLOBAL_COVERAGE': GLOBAL_COVERAGE,
                                 })
        self.write_files(ctx)

    def write_module_coverage_file(self, app, moduleName, sourceFileName, num_of_lines, not_covered_lines = [], excluded_lines = []):
        ''' Set and writes the coverage report '''
        from django.template import Context
        from django.template.loader import get_template
        #Decode a file
        fo = codecs.open(sourceFileName, 'rb', "utf-8")
        try:
            source = fo.read()
        finally:
            fo.close()

        try:
            offset = 0
            lines = source.split("\n")
            while lines[ offset ] == "":
                offset += 1
                if offset > 0:
                    not_covered_lines = [x - 1 for x in not_covered_lines]
        except IndexError:
            offset = 0

        #Lexer tokenize an input string
        lexer = get_lexer_by_name("py")

        tokens = lex(source, lexer)
        fmt = CssHtmlFormatter(linenos = 'inline', hl_lines = not_covered_lines, noclasses = False, css_lines = {"skipped" : excluded_lines})
        fmt.lineseparator = "\n"
        source_html = format(tokens, fmt)

        ncl = len(not_covered_lines) # uncovered lines
        cl = num_of_lines - ncl # number covered lines
        el = len(excluded_lines)
        co = cl > 0 and float(cl * 100 / num_of_lines) or 0

        t = get_template('coverage_module.tpl.html')
        now = datetime.datetime.now()
        html = t.render(Context({'now': now,
                                 'module':moduleName,
                                 'app':moduleName.split('.')[0],
                                 'pkgs':moduleName.split("."),
                                 'tl': num_of_lines,
                                 'cl': cl,
                                 'el': el,
                                 'co': co,
                                 'title': "%s coverage" % moduleName,
                                 'code': source_html,
                                 'GLOBAL_COVERAGE': GLOBAL_COVERAGE,
                                 }))

        fp = self.get_file_handle(app, moduleName)
        fp.write(html.encode('utf-8'))
        fp.close()

    def enabled(self, modname):
        ''' Verifies that the module is enabled  '''
        return (modname in self.valid_rexx) and (modname not in self.skip_rexx) 

    def get_file_handle(self, app, filename):
        return file(self.get_file_name(app, filename), "wb")

    def get_file_name(self, app, filename):
        """ return fullfilename  BASE/application_name/ """
        targetDir = os.path.join(self.output_dir, app)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir)
        return os.path.join(targetDir, filename + ".html")

    def _setup_dest_directory(self, options):
        '''Creates the coverage directory '''
        from django.conf import settings
        dest = options.pop('dest_dir', getattr(settings, "COVERAGE_DIR", os.path.join(os.path.pardir, "coverage_dir")))
        self.output_dir = os.path.abspath(dest)
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        print "Save coverage data in:" , self.output_dir

    def _setup_regex(self):
        ''' Defines exclusion rules for files '''
        from django.test import simple
        from django.conf import settings

        self.valid_rexx = RegExpList()
        for el in self.mod_enabled:
            self.valid_rexx.append("^" + el + ".*")


        self.skip_rexx = RegExpList( getattr(settings, "COVERAGE_SKIP", 
                                             [ ".*tests.*", 
                                              ".*\.%s\..*" % simple.TEST_MODULE, 
                                              ".*\.%s" % simple.TEST_MODULE, 
                                              "^django\..*", 
#                                              ".*\.coverage", 
#                                              "^django_evolution\..*", 
#                                              "^mychecker", 
#                                              "^djangodevtools\..*" 
                                                ]
                                             )
                                        )
#        for el in 
#            self.skip_rexx.append(rel )

    def html_report(self, cov):
        '''Analyzes python modules to set the coverage report'''
        from django.contrib.admin.sites import AlreadyRegistered

        self._setup_regex()
        modules = sys.modules.keys()
        ttl = 0 # total valid statements lines
        tcl = 0 # total covered lines
        tel = 0 # total excluded lines
        self.summary_data = AppDataDict()
        self.summary_data[ GLOBAL_COVERAGE ] = "All"
        for modname in modules:
            if self.enabled(modname):
                try:
                    module = __import__(modname, globals(), locals(), [""])
                    filename, statements, excluded, missing, _missing_formatted = cov.analysis2(module)
                    tl = len(statements) # total lines of code
                    if tl > 0:
                        ncl = len(missing) # uncovered lines
                        el = len(excluded) # excluded lines
                        cl = tl - ncl # number covered lines
                        co = cl * 100. / tl if cl > 0 else 0. #module coverage
                        app = modname.split('.')[0]
                        self.summary_data[ app ] = ""

                        ttl += tl
                        tcl += cl
                        tel += el

                        data = (co, modname, tl, cl, el, app)
                        self.summary_data[ app ].update(tl, ncl, el, data)
                        self.summary_data[ GLOBAL_COVERAGE ].update(tl, ncl, el, data)

                        self.write_module_coverage_file(app, modname, filename, tl, missing, excluded)
                except ImportError:
                    pass
                except ValueError:
                    pass
                except AlreadyRegistered:
                    pass
        self.write_index(ttl, tcl, tel)
