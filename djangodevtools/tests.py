# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''

from unittest import TestCase
from subprocess import Popen, PIPE, STDOUT
import shutil
import os

class Test(TestCase):
    """
    very quick and dirty test. Only to check import and refactoring issue.
    TODO: create a sample app and run test against
    """
    def setUp(self):
        if os.path.exists('manage.cfg'):
            shutil.move('manage.cfg', 'manage.backup')
    
    def tearDown(self):
        if os.path.exists('manage.backup'):
            shutil.move('manage.backup', 'manage.cfg')
    
    def _run(self, *args, **kwargs):
        cmd = ['python', 'manage.py']
        _out = kwargs.get('stdout', PIPE)
        _err = kwargs.get('stderr', STDOUT)

        cmd.extend(args)
        p = Popen(cmd, stdout=_out, stderr=_err)
        stdoutdata, stderrdata = p.communicate()
        return p.returncode, [stdoutdata, stderrdata]

    def test_cc(self):
        p, out = self._run('cc')
        self.assertEqual(p, 0, out)

    def test_alias_create(self):
        p, out = self._run('alias', 'tt=sqlclear polls')
        self.assertEqual(p, 0, out)
        p, out = self._run('tt')        
        self.assertEqual(out[0], r"""BEGIN;
DROP TABLE "polls_choice";
DROP TABLE "polls_poll";
COMMIT;
""")

    def test_alias_remove(self):
        p, out = self._run('alias', 'tt=sqlclear polls')
        self.assertEqual(p, 0, out)
        p, out = self._run('tt')        
        self.assertEqual(out[0], r"""BEGIN;
DROP TABLE "polls_choice";
DROP TABLE "polls_poll";
COMMIT;
""")

    def xtest_cover(self):
        p, out = self._run('cover', 'test', 'djangodevtools.Test.test_cc')
        self.assertEqual(p, 0, out)

    def test_flakes(self):
        p, out = self._run('flakes', 'djangodevtools', '-i', 
                           '.*redefinition ', '-i', '.*SeleniumTestRunner', '-i','.*local variable')
        self.assertEqual(p, 0, out)

    def test_zap(self):
        p, out = self._run('zap', '--help')
        self.assertEqual(p, 0, out)

    def test_jsmin(self):
        p, out = self._run('jsmin', '--help')
        self.assertEqual(p, 0, out)

    def test_pep8(self):
        p, out = self._run('p8', 'djangodevtools')
        self.assertEqual(p, 0, out)
