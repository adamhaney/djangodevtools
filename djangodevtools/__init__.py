# -*- coding: utf-8 -*-
'''
Django Development Tools
http://www.os4d.org/djangodevtools/

'''
VERSION = (0, 4, 0, 'dev', 0)


def get_svn_revision():
    import re
    import os
    rev = u'0'
    entries_path = '%s/.svn/entries' % os.path.dirname(__file__)
    try:
        entries = open(entries_path, 'r').read()
    except IOError:
        pass
    else:
        if re.match('(\d+)', entries):
            rev_match = re.search('\d+\s+dir\s+(\d+)', entries)
            if rev_match:
                rev = rev_match.groups()[0]

    return u'%s' % rev


def get_version():
    version = '%s.%s.%s %s' % VERSION[:-1]
    svn_rev = get_svn_revision()

    return "%s %s" % (version, svn_rev)


def manage_enable_alias():
    from django.core import management as mgm

    def alias_get_commands():
        """
            monkeypatch to handle aliases directly as extra commands
            of manage.py.

            to activate put following lines in your settings.py :
            from djangodevtools import manage_enable_alias
            manage_enable_alias()

        """
        if not mgm._commands:
            backup_get_command()
            from djangodevtools.management.commands.alias import \
                                    Command as Alias
            Alias.patched = True
            mgm._commands.update(unalias=Alias("unalias"))
            mgm._aliases = Alias.commands()
            mu = mgm.ManagementUtility()
            for alias in mgm._aliases.keys():
                if alias in mgm._commands.keys():
                    mgm._commands["%s/c" % alias] = mu.fetch_command(alias)

            mgm._pure_commands = dict(mgm._commands)
            mgm._commands.update(mgm._aliases)
        return mgm._commands

    def main_help_text(self):
        """
        Returns the script's main help text, as a string.
        """
        usage = ['',
                 "Type '%s help <subcommand>' "
                 "for help on a specific subcommand." % self.prog_name,
                 '',
                 'Available subcommands:']
        #usage.append()
        mgm.get_commands()
        commands = mgm._pure_commands.keys()
        commands.sort()
        aliases = mgm._aliases.keys()
        aliases.sort()

        for cmd in commands:
            if cmd in aliases:
                usage.append('  #%s (overrided by aliases)' % cmd)
            elif "/c" in cmd:
                usage.append('  %s (original %s)' %
                                (cmd, cmd.replace("/c", "")))
            else:
                usage.append('  %s' % cmd)

        if aliases:
            usage.append('\nAvailable Aliases:')
        for cmd in aliases:
            usage.append('  %s' % cmd)

        return '\n'.join(usage)
    mgm.get_commands, backup_get_command = alias_get_commands, mgm.get_commands
    mgm.ManagementUtility.main_help_text = main_help_text


def manage_enable_coverage():
    def fetch_command(self, subcommand):
        """
            monkeypatch to quickly run a coverage command before django
            loads the applications

            to activate put following lines in your settings.py :
            from djangodevtools import manage_enable_coverage
            manage_enable_coverage()

        """
        if subcommand == "cover":
            from djangodevtools.management.commands.cover import \
                                                Command as Cover
            return Cover()
        else:
            return backup_fetch_command(self, subcommand)

    from django.core.management import ManagementUtility as m
    m.fetch_command, backup_fetch_command = fetch_command, m.fetch_command
