from djangodevtools.wsgitest import DSTEST_PATH, kill_process_tree
from django.conf import settings
from djangodevtools.wsgitest import WsgiTestRunner
from subprocess import Popen, PIPE
import os
import re
import threading

class SeleniumRCThread(threading.Thread):
    """Selenium RC control thread."""
    def __init__(self, server_filepath, server_port):
        super(SeleniumRCThread, self).__init__()
        self.server_filepath = server_filepath
        self.server_port = server_port
        self.process = None

    def run(self):
        """Launch Selenium server."""
        self.process = Popen(('java -jar %s -port %s' % (self.server_filepath, self.server_port)).split(),
            shell=False) #, stdout=PIPE, stderr=PIPE)

    def stop(self):
        """Stop Selenium server."""
        kill_process_tree(self.process)


class SeleniumTestRunner(WsgiTestRunner):
    def __init__(self, verbosity=0, interactive=False, failfast=False):
        super(SeleniumTestRunner, self).__init__(verbosity=0, interactive=False, failfast=False)
        self.test_module = getattr(settings, 'SELENIUM_TEST_MODULE', 'tests.selenium')
        
        self.rc_path = os.path.join(DSTEST_PATH, 'selenium-server.jar')
        self.starting_selenium = getattr(settings, "SELENIUM_START", True)
        self.selenium_port = getattr(settings, "SELENIUM_PORT", 4444)
        
        if not self._dependencies_met():
            raise Exception("Not met dependency...")
        
    def setup_test_environment(self):
        super(SeleniumTestRunner, self).setup_test_environment()
        if self.starting_selenium:
            print 'Starting selenium server.'    
            self.selenium_rc = SeleniumRCThread(self.rc_path, self.selenium_port)
            self.selenium_rc.start()
    
    def teardown_test_environment(self):
        super(SeleniumTestRunner, self).teardown_test_environment()
        if self.starting_selenium:
            self.selenium_rc.stop()

    def _dependencies_met(self):
        """Check Selenium testing dependencies are met"""
        # Check Java VM command line runner.
        if self.starting_selenium:
            try:
                Popen(['java', '-version'], shell=False, stderr=PIPE).communicate()[1]
            except:
                print 'Dependecy unmet. Java virtual machine command line runner not ' \
                    'found.'
                return False
            # Check selenium-server.jar is ready to run.
            output = Popen(('java -jar %s -unrecognized_argument' % self.rc_path
                ).split(), shell=False, stderr=PIPE).communicate()[1]
            if not re.search('Usage: java -jar selenium-server.jar', output):
                print 'Dependecy unmet. Selenium RC server (selenium-server.jar) not ' \
                    'found.'
                return False
        return True