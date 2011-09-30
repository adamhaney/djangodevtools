# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
from django.core.management.base import BaseCommand
import os
import sys
#from djangodevtools.externals.configobj import ConfigObj
from configobj import ConfigObj

from django.core.management import ManagementUtility
from django.utils.encoding import smart_str

CFG_FILE = "manage.cfg"


class Command(BaseCommand):
    '''
    Save commands and parameters as shortcuts. 
    Based on setuptools aliases feature.
    '''
    patched = False


    @classmethod
    def commands(cls):
        return dict([(cmd,cls(cmd)) for cmd in cls()])

    def usage_alias(self, subcommand):
        return """
    ./manage.py %(subcommand)s

%(help)s

This alias run the following commands:
\t./manage.py %(cmds)s

            """ % dict(subcommand=subcommand,
                       cmds="\n\t./manage.py ".join([x.strip() for x in self.cfg["aliases"].get(subcommand, "").split(";")]),
                       help=self.get_help(subcommand))

    def usage(self, subcommand):
        """
        Return a brief description of how to use this command, by
        default from the attribute ``self.help``.
        """
        if subcommand == self.run_alias:
            return self.usage_alias(subcommand)
        return """
    ./manage.py alias
    ./manage.py alias name
    ./manage.py alias name[=value]
    ./manage.py unalias name

    Save commands and parameters as shortcuts.
    Aliases are stored in '%s' in the same directory of 'manage.py'.

    Aliases Usage:
        ./manage.py name
        """ % CFG_FILE

    def get_help(self, subcommand):
        return self.cfg["help"].get(subcommand, "").replace(r"\n", "\n").replace(r"\t", "\t")

    def __init__(self, alias=None):
        super(Command, self).__init__()
        config_file = os.path.join(os.path.realpath( os.path.dirname(sys.argv[0]) ), CFG_FILE)
        self.cfg= ConfigObj(config_file, create_empty=True)
        self.cfg['aliases'] = self.cfg.get('aliases', {})
        self.cfg['help'] = self.cfg.get('help', {})
        self.run_alias = alias


    def __contains__(self, target):
        return target in self.cfg['aliases'].keys()        

    def __getitem__(self, target):
        return self.cfg['aliases'].keys()[target]

    def _list(self, cmd=None):
        items = self.cfg['aliases'].items()
        if items:
            if not cmd:
                try:
                    print "\nAliases:"
                    for k,v in items:
                        print "%-5s : %s" % (k, v)
                    print
                except KeyError:
                    pass
            else:
                value = self.cfg['aliases'].get(cmd, None)
                if value:
                    print "%-5s : %s" % (cmd, value)
                else:
                    sys.stderr.write(smart_str(self.style.ERROR("Alias '%s' not found !!\n" % cmd)))
        else:
            self.print_help(None, "alias")

    def exists(self):
        #return self.run_alias == "unalias" or self.cfg['aliases'].has_key(self.run_alias)
        return self.run_alias == "unalias" or self.run_alias in self

    def execute_alias(self, alias=None):
        alias = alias or self.run_alias
        cmd = self.cfg['aliases'][alias]
        commands = cmd.split(';')
        for cmd in commands:
            elements = cmd.strip().split(' ')
            elements.insert(0, "manage.py")
            # TODO manage settings
            ManagementUtility(elements).fetch_command(elements[1]).run_from_argv(elements)

            
    def checks(self, cmd, commands):
        try:
            if cmd in ["alias"]:
                return False

            #for subcmd in commands.split(";"):
            #    if cmd == subcmd.strip().split(" ")[0]:
            #        return False
        except:
            raise
            return False
        return True


    def handle(self, cmd=None, *args, **options):
        if not self.patched:
            print """
    Alias command is not enabled.
                    
    In order to use alias command please put following lines in your settings.py:

        from djangodevtools import manage_enable_alias
        manage_enable_alias()
            """
            return


        if self.run_alias == "unalias":
            self.cfg['aliases'].pop(cmd, None)
            self.cfg.write()
        elif self.run_alias:
            self.execute_alias()
        else:
            try:
                if cmd:
                    if "=" in cmd:
                        cmd, commands = cmd.split("=", 1)
                        if commands:
                            if self.checks(cmd, commands):
                                self.cfg['aliases'][cmd] = commands
                            else:
                                print "Please check %s=%s\nIt's invalid" % (cmd, commands)
                        else:
                            self.cfg['aliases'].pop(cmd, None)
                        self.cfg.write()
                    else:
                        self._list(cmd)
                else:
                    self._list()
            except KeyError:
                sys.stderr.write(smart_str(self.style.ERROR("Alias '%s' not found !!\n" % args[0])))

class UnAlias(Command):
    def handle(self, cmd=None, *args, **options):
        self.cfg['aliases'].pop(cmd, None)
        self.cfg.write()