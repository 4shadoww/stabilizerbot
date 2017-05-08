# -*- coding: utf-8  -*-
"""User-interface related functions for building bots."""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id: feaa3d5786f5b4cad37e58f6158372483304b875 $'

# Note: the intention is to develop this module (at some point) into a Bot
# class definition that can be subclassed to create new, functional bot
# scripts, instead of writing each one from scratch.

# Note: all output goes thru python std library "logging" module

import codecs
import datetime
import json
import logging
import logging.handlers
import os
import re
import sys
import time
import warnings
import webbrowser

_logger = "bot"

# logging levels
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
STDOUT = 16
VERBOSE = 18
INPUT = 25

import pywikibot

from pywikibot import backports
from pywikibot import config
from pywikibot import daemonize
from pywikibot import version
from pywikibot.tools import deprecated, deprecated_args

if sys.version_info[0] > 2:
    unicode = str

# User interface initialization
# search for user interface module in the 'userinterfaces' subdirectory
uiModule = __import__("pywikibot.userinterfaces.%s_interface"
                      % config.userinterface,
                      fromlist=['UI'])
ui = uiModule.UI()
pywikibot.argvu = ui.argvu()


# Logging module configuration
class RotatingFileHandler(logging.handlers.RotatingFileHandler):

    """Modified RotatingFileHandler supporting unlimited amount of backups."""

    def doRollover(self):
        """
        Modified naming system for logging files.

        Overwrites the default Rollover renaming by inserting the count number
        between file name root and extension. If backupCount is >= 1, the system
        will successively create new files with the same pathname as the base
        file, but with inserting ".1", ".2" etc. in front of the filename
        suffix. For example, with a backupCount of 5 and a base file name of
        "app.log", you would get "app.log", "app.1.log", "app.2.log", ...
        through to "app.5.log". The file being written to is always "app.log" -
        when it gets filled up, it is closed and renamed to "app.1.log", and if
        files "app.1.log", "app.2.log" etc. already exist, then they are
        renamed to "app.2.log", "app.3.log" etc. respectively.
        If backupCount is == -1 do not rotate but create new numbered filenames.
        The newest file has the highest number except some older numbered files
        where deleted and the bot was restarted. In this case the ordering
        starts from the lowest available (unused) number.

        """
        if self.stream:
            self.stream.close()
            self.stream = None
        root, ext = os.path.splitext(self.baseFilename)
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = "%s.%d%s" % (root, i, ext)
                dfn = "%s.%d%s" % (root, i + 1, ext)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = "%s.1%s" % (root, ext)
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        elif self.backupCount == -1:
            if not hasattr(self, '_lastNo'):
                self._lastNo = 1
            while True:
                fn = "%s.%d%s" % (root, self._lastNo, ext)
                self._lastNo += 1
                if not os.path.exists(fn):
                    break
            os.rename(self.baseFilename, fn)
        self.mode = 'w'
        self.stream = self._open()

    def format(self, record):
        """Strip trailing newlines before outputting text to file."""
        # Warnings captured from the warnings system are not processed by
        # logoutput(), so the 'context' variables are missing.
        # The same context details are provided by Python 3.X, but need to
        # be extracted from the warning message for Python <= 2.7.
        if record.name == 'py.warnings' and 'caller_file' not in record.__dict__:
            assert(len(record.args) == 1)
            msg = record.args[0]

            if sys.version_info[0] < 3:
                record.pathname = msg.partition(':')[0]
                record.lineno = msg.partition(':')[2].partition(':')[0]
                record.module = msg.rpartition('/')[2].rpartition('.')[0]
            else:
                assert(msg.startswith(record.pathname + ':'))

            record.__dict__['caller_file'] = record.pathname
            record.__dict__['caller_name'] = record.module
            record.__dict__['caller_line'] = record.lineno

            # Remove the path and the line number, and strip the extra space
            msg = msg.partition(':')[2].partition(':')[2].lstrip()
            record.args = (msg,)

        text = logging.handlers.RotatingFileHandler.format(self, record)
        return text.rstrip("\r\n")


class LoggingFormatter(logging.Formatter):

    """Format LogRecords for output to file.

    This formatter *ignores* the 'newline' key of the LogRecord, because
    every record written to a file must end with a newline, regardless of
    whether the output to the user's console does.

    """

    def formatException(self, ei):
        r"""
        Convert exception trace to unicode if necessary.

        Make sure that the exception trace is converted to unicode.

        L{exceptions.Error} traces are encoded in our console encoding, which
        is needed for plainly printing them.  However, when logging them
        using logging.exception, the Python logging module will try to use
        these traces, and it will fail if they are console encoded strings.

        Formatter.formatException also strips the trailing \n, which we need.
        """
        strExc = logging.Formatter.formatException(self, ei)

        if sys.version_info[0] < 3 and isinstance(strExc, str):
            return strExc.decode(config.console_encoding) + '\n'
        else:
            return strExc + '\n'


# Initialize the handlers and formatters for the logging system.
#
# This relies on the global variable 'ui' which is a UserInterface object
# defined in the 'userinterface' subpackage.
#
# The UserInterface object must define its own init_handlers() method
# which takes the root logger as its only argument, and which adds to that
# logger whatever handlers and formatters are needed to process output and
# display it to the user.  The default (terminal) interface sends level
# STDOUT to sys.stdout (as all interfaces should) and sends all other
# levels to sys.stderr; levels WARNING and above are labeled with the
# level name.
#
# UserInterface objects must also define methods input(), input_choice(),
# editText(), and askForCaptcha(), all of which are documented in
# userinterfaces/terminal_interface.py

_handlers_initialized = False


def init_handlers(strm=None):
    """Initialize logging system for terminal-based bots.

    This function must be called before using pywikibot.output(); and must
    be called again if the destination stream is changed.

    Note: this function is called by handleArgs(), so it should normally
    not need to be called explicitly

    All user output is routed through the logging module.
    Each type of output is handled by an appropriate handler object.
    This structure is used to permit eventual development of other
    user interfaces (GUIs) without modifying the core bot code.

    The following output levels are defined:
     - DEBUG: only for file logging; debugging messages.
     - STDOUT: output that must be sent to sys.stdout (for bots that may
         have their output redirected to a file or other destination).
     - VERBOSE: optional progress information for display to user.
     - INFO: normal (non-optional) progress information for display to user.
     - INPUT: prompts requiring user response.
     - WARN: user warning messages.
     - ERROR: user error messages.
     - CRITICAL: fatal error messages.

    Accordingly, do ''not'' use print statements in bot code; instead,
    use pywikibot.output function.

    @param strm: Output stream. If None, re-uses the last stream if one
        was defined, otherwise uses sys.stderr

    """
    global _handlers_initialized

    moduleName = calledModuleName()
    if not moduleName:
        moduleName = "terminal-interface"

    logging.addLevelName(VERBOSE, "VERBOSE")
    # for messages to be displayed on terminal at "verbose" setting
    # use INFO for messages to be displayed even on non-verbose setting

    logging.addLevelName(STDOUT, "STDOUT")
    # for messages to be displayed to stdout

    logging.addLevelName(INPUT, "INPUT")
    # for prompts requiring user response

    root_logger = logging.getLogger("pywiki")
    root_logger.setLevel(DEBUG + 1)  # all records except DEBUG go to logger

    warnings_logger = logging.getLogger("py.warnings")
    warnings_logger.setLevel(DEBUG)

    # If there are command line warnings options, do not override them
    if not sys.warnoptions:
        if hasattr(logging, 'captureWarnings'):
            logging.captureWarnings(True)  # introduced in Python >= 2.7
        else:
            backports.captureWarnings(True)

        if config.debug_log or 'deprecation' in config.log:
            warnings.filterwarnings("always")
        elif config.verbose_output:
            warnings.filterwarnings("module")

    root_logger.handlers = []  # remove any old handlers

    # configure handler(s) for display to user interface
    ui.init_handlers(root_logger, **config.userinterface_init_kwargs)

    # if user has enabled file logging, configure file handler
    if moduleName in config.log or '*' in config.log:
        if config.logfilename:
            logfile = config.datafilepath("logs", config.logfilename)
        else:
            logfile = config.datafilepath("logs", "%s-bot.log" % moduleName)
        file_handler = RotatingFileHandler(filename=logfile,
                                           maxBytes=1024 * config.logfilesize,
                                           backupCount=config.logfilecount)

        file_handler.setLevel(DEBUG)
        form = LoggingFormatter(
            fmt="%(asctime)s %(caller_file)18s, %(caller_line)4s "
                "in %(caller_name)18s: %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(form)
        root_logger.addHandler(file_handler)
        # Turn on debugging for each component requested by user
        # or for all components if nothing was specified
        for component in config.debug_log:
            if component:
                debuglogger = logging.getLogger("pywiki." + component)
            else:
                debuglogger = logging.getLogger("pywiki")
            debuglogger.setLevel(DEBUG)
            debuglogger.addHandler(file_handler)

        warnings_logger.addHandler(file_handler)

    _handlers_initialized = True

    pywikibot.tools.debug = debug

    writelogheader()


def writelogheader():
    """
    Save additional version, system and status info to the log file in use.

    This may help the user to track errors or report bugs.
    """
    # If a http thread is not available, it's too early to print a header
    # that includes version information, which may need to query a server.
    # The http module can't be imported due to circular dependencies.
    http = sys.modules.get('pywikibot.comms.http', None)
    if not http or not hasattr(http, 'threads') or not len(http.threads):
        return

    log(u'=== Pywikibot framework v2.0 -- Logging header ===')

    # script call
    log(u'COMMAND: {0}'.format(sys.argv))

    # script call time stamp
    log(u'DATE: %s UTC' % str(datetime.datetime.utcnow()))

    # new framework release/revision? (handleArgs needs to be called first)
    try:
        log(u'VERSION: %s' %
            version.getversion(online=config.log_pywiki_repo_version).strip())
    except version.ParseError:
        exception()

    # system
    if hasattr(os, 'uname'):
        log(u'SYSTEM: {0}'.format(os.uname()))

    # config file dir
    log(u'CONFIG FILE DIR: %s' % pywikibot.config2.base_dir)

    all_modules = sys.modules.keys()

    # These are the main dependencies of pywikibot.
    check_package_list = ['httplib2', 'mwparserfromhell']

    # report all imported packages
    if config.verbose_output:
        check_package_list += all_modules

    packages = version.package_versions(check_package_list)

    log(u'PACKAGES:')
    for name in sorted(packages.keys()):
        info = packages[name]
        if 'path' not in info:
            if 'type' in info:
                info['path'] = '[' + info['type'] + ']'
            else:
                info['path'] = '[path unknown]'
        if 'ver' not in info:
            info['ver'] = '??'
        if 'err' in info:
            log(u'  %(name)s: %(err)s' % info)
        else:
            log(u'  %(name)s (%(path)s) = %(ver)s' % info)

    # imported modules
    log(u'MODULES:')
    for module in sys.modules.values():
        filename = version.get_module_filename(module)
        ver = version.get_module_version(module)
        mtime = version.get_module_mtime(module)
        if filename and ver and mtime:
            # it's explicitly using str() to bypass unicode_literals in Python 2
            # isoformat expects a char not a unicode in Python 2
            log(u'  {0} {1} {2}'.format(filename, ver[:7], mtime.isoformat(str(' '))))

    if config.log_pywiki_repo_version:
        log(u'PYWIKI REPO VERSION: %s' % version.getversion_onlinerepo())

    log(u'=== ' * 14)


# User output/logging functions

# Six output functions are defined. Each requires a unicode or string
# argument.  All of these functions generate a message to the log file if
# logging is enabled ("-log" or "-debug" command line arguments).

# The functions output(), stdout(), warning(), and error() all display a
# message to the user through the logger object; the only difference is the
# priority level,  which can be used by the application layer to alter the
# display. The stdout() function should be used only for data that is
# the "result" of a script, as opposed to information messages to the
# user.

# The function log() by default does not display a message to the user, but
# this can be altered by using the "-verbose" command line option.

# The function debug() only logs its messages, they are never displayed on
# the user console. debug() takes a required second argument, which is a
# string indicating the debugging layer.

def logoutput(text, decoder=None, newline=True, _level=INFO, _logger="",
              **kwargs):
    """Format output and send to the logging module.

    Helper function used by all the user-output convenience functions.

    """
    if _logger:
        logger = logging.getLogger("pywiki." + _logger)
    else:
        logger = logging.getLogger("pywiki")

    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    # frame 0 is logoutput() in this module,
    # frame 1 is the convenience function (output(), etc.)
    # frame 2 is whatever called the convenience function
    frame = sys._getframe(2)

    module = os.path.basename(frame.f_code.co_filename)
    context = {'caller_name': frame.f_code.co_name,
               'caller_file': module,
               'caller_line': frame.f_lineno,
               'newline': ("\n" if newline else "")}

    if decoder:
        text = text.decode(decoder)
    elif not isinstance(text, unicode):
        if not isinstance(text, str):
            # looks like text is a non-text object.
            # Maybe it has a __unicode__ builtin ?
            # (allows to print Page, Site...)
            text = unicode(text)
        else:
            try:
                text = text.decode('utf-8')
            except UnicodeDecodeError:
                text = text.decode('iso8859-1')

    logger.log(_level, text, extra=context, **kwargs)


def output(text, decoder=None, newline=True, toStdout=False, **kwargs):
    r"""Output a message to the user via the userinterface.

    Works like print, but uses the encoding used by the user's console
    (console_encoding in the configuration file) instead of ASCII.

    If decoder is None, text should be a unicode string. Otherwise it
    should be encoded in the given encoding.

    If newline is True, a line feed will be added after printing the text.

    If toStdout is True, the text will be sent to standard output,
    so that it can be piped to another process. All other text will
    be sent to stderr. See: https://en.wikipedia.org/wiki/Pipeline_%28Unix%29

    text can contain special sequences to create colored output. These
    consist of the escape character \03 and the color name in curly braces,
    e. g. \03{lightpurple}. \03{default} resets the color.

    Other keyword arguments are passed unchanged to the logger; so far, the
    only argument that is useful is "exc_info=True", which causes the
    log message to include an exception traceback.

    """
    if toStdout:  # maintained for backwards-compatibity only
        logoutput(text, decoder, newline, STDOUT, **kwargs)
    else:
        logoutput(text, decoder, newline, INFO, **kwargs)


def stdout(text, decoder=None, newline=True, **kwargs):
    """Output script results to the user via the userinterface."""
    logoutput(text, decoder, newline, STDOUT, **kwargs)


def warning(text, decoder=None, newline=True, **kwargs):
    """Output a warning message to the user via the userinterface."""
    logoutput(text, decoder, newline, WARNING, **kwargs)


def error(text, decoder=None, newline=True, **kwargs):
    """Output an error message to the user via the userinterface."""
    logoutput(text, decoder, newline, ERROR, **kwargs)


def log(text, decoder=None, newline=True, **kwargs):
    """Output a record to the log file."""
    logoutput(text, decoder, newline, VERBOSE, **kwargs)


def critical(text, decoder=None, newline=True, **kwargs):
    """Output a critical record to the log file."""
    logoutput(text, decoder, newline, CRITICAL, **kwargs)


def debug(text, layer, decoder=None, newline=True, **kwargs):
    """Output a debug record to the log file.

    @param layer: The name of the logger that text will be sent to.
    """
    logoutput(text, decoder, newline, DEBUG, layer, **kwargs)


def exception(msg=None, decoder=None, newline=True, tb=False, **kwargs):
    """Output an error traceback to the user via the userinterface.

    Use directly after an 'except' statement::

        ...
        except:
            pywikibot.exception()
        ...

    or alternatively::

        ...
        except Exception as e:
            pywikibot.exception(e)
        ...

    @param tb: Set to True in order to output traceback also.
    """
    if isinstance(msg, BaseException):
        exc_info = 1
    else:
        exc_info = sys.exc_info()
        msg = u'%s: %s' % (repr(exc_info[1]).split('(')[0],
                           unicode(exc_info[1]).strip())
    if tb:
        kwargs['exc_info'] = exc_info
    logoutput(msg, decoder, newline, ERROR, **kwargs)


# User input functions


def input(question, password=False, default='', force=False):
    """Ask the user a question, return the user's answer.

    @param question: a string that will be shown to the user. Don't add a
        space after the question mark/colon, this method will do this for you.
    @type question: unicode
    @param password: if True, hides the user's input (for password entry).
    @type password: bool
    @param default: The default answer if none was entered. None to require
        an answer.
    @type default: basestring
    @param force: Automatically use the default
    @type force: bool
    @rtype: unicode
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    data = ui.input(question, password=password, default=default, force=force)
    return data


def input_choice(question, answers, default=None, return_shortcut=True,
                 automatic_quit=True, force=False):
    """
    Ask the user the question and return one of the valid answers.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param answers: The valid answers each containing a full length answer and
        a shortcut. Each value must be unique.
    @type answers: Iterable containing an iterable of length two
    @param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None. If it should
        be linked with the valid answers it must be its shortcut.
    @type default: basestring
    @param return_shortcut: Whether the shortcut or the index of the answer is
        returned.
    @type return_shortcut: bool
    @param automatic_quit: Adds the option 'Quit' ('q') and throw a
            L{QuitKeyboardInterrupt} if selected.
    @type automatic_quit: bool
    @param force: Automatically use the default
    @type force: bool
    @return: The selected answer shortcut or index. Is -1 if the default is
        selected, it does not return the shortcut and the default is not a
        valid shortcut.
    @rtype: int (if not return shortcut), basestring (otherwise)
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    return ui.input_choice(question, answers, default, return_shortcut,
                           automatic_quit=automatic_quit, force=force)


def input_yn(question, default=None, automatic_quit=True, force=False):
    """
    Ask the user a yes/no question and returns the answer as a bool.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param default: The result if no answer was entered. It must be a bool or
        'y' or 'n' and can be disabled by setting it to None.
    @type default: basestring or bool
    @param automatic_quit: Adds the option 'Quit' ('q') and throw a
            L{QuitKeyboardInterrupt} if selected.
    @type automatic_quit: bool
    @param force: Automatically use the default
    @type force: bool
    @return: Return True if the user selected yes and False if the user
        selected no. If the default is not None it'll return True if default
        is True or 'y' and False if default is False or 'n'.
    @rtype: bool
    """
    if default not in ['y', 'Y', 'n', 'N']:
        if default:
            default = 'y'
        elif default is not None:
            default = 'n'
    assert default in ['y', 'Y', 'n', 'N', None]

    return input_choice(question, [('Yes', 'y'), ('No', 'n')], default,
                        automatic_quit=automatic_quit, force=force) == 'y'


@deprecated('input_choice')
def inputChoice(question, answers, hotkeys, default=None):
    """Ask the user a question with several options, return the user's choice.

    DEPRECATED: Use L{input_choice} instead!

    The user's input will be case-insensitive, so the hotkeys should be
    distinctive case-insensitively.

    @param question: a string that will be shown to the user. Don't add a
        space after the question mark/colon, this method will do this for you.
    @type question: basestring
    @param answers: a list of strings that represent the options.
    @type answers: list of basestring
    @param hotkeys: a list of one-letter strings, one for each answer.
    @param default: an element of hotkeys, or None. The default choice that will
                 be returned when the user just presses Enter.
    @return: a one-letter string in lowercase.
    @rtype: str
    """
    # make sure logging system has been initialized
    if not _handlers_initialized:
        init_handlers()

    return ui.input_choice(question=question, options=zip(answers, hotkeys),
                           default=default, return_shortcut=True,
                           automatic_quit=False)


def input_list_choice(question, answers, default=None,
                      automatic_quit=True, force=False):
    """
    Ask the user the question and return one of the valid answers.

    @param question: The question asked without trailing spaces.
    @type question: basestring
    @param answers: The valid answers each containing a full length answer.
    @type answers: Iterable of basestring
    @param default: The result if no answer was entered. It must not be in the
        valid answers and can be disabled by setting it to None.
    @type default: basestring
    @param force: Automatically use the default
    @type force: bool
    @return: The selected answer.
    @rtype: basestring
    """
    if not _handlers_initialized:
        init_handlers()

    return ui.input_list_choice(question, answers, default=default,
                                force=force)


# Command line parsing and help
def calledModuleName():
    """Return the name of the module calling this function.

    This is required because the -help option loads the module's docstring
    and because the module name will be used for the filename of the log.

    @rtype: unicode
    """
    # get commandline arguments
    called = pywikibot.argvu[0].strip()
    if ".py" in called:  # could end with .pyc, .pyw, etc. on some platforms
        # clip off the '.py?' filename extension
        called = called[:called.rindex('.py')]
    return os.path.basename(called)


def handle_args(args=None, do_help=True):
    """
    Handle standard command line arguments, and return the rest as a list.

    Takes the command line arguments as Unicode strings, processes all
    global parameters such as -lang or -log, initialises the logging layer,
    which emits startup information into log at level 'verbose'.

    This makes sure that global arguments are applied first,
    regardless of the order in which the arguments were given.

    args may be passed as an argument, thereby overriding sys.argv

    @param args: Command line arguments
    @type args: list of unicode
    @param do_help: Handle parameter '-help' to show help and invoke sys.exit
    @type do_help: bool
    @return: list of arguments not recognised globally
    @rtype: list of unicode
    """
    # get commandline arguments if necessary
    if not args:
        # it's the version in pywikibot.__init__ that is changed by scripts,
        # not the one in pywikibot.bot.
        args = pywikibot.argvu[1:]
    # get the name of the module calling this function. This is
    # required because the -help option loads the module's docstring and because
    # the module name will be used for the filename of the log.
    moduleName = calledModuleName()
    if not moduleName:
        moduleName = "terminal-interface"
    nonGlobalArgs = []
    username = None
    do_help = None if do_help else False
    for arg in args:
        if do_help is not False and arg == '-help':
            do_help = True
        elif arg.startswith('-dir:'):
            pass
        elif arg.startswith('-family:'):
            config.family = arg[len("-family:"):]
        elif arg.startswith('-lang:'):
            config.mylang = arg[len("-lang:"):]
        elif arg.startswith("-user:"):
            username = arg[len("-user:"):]
        elif arg.startswith('-putthrottle:'):
            config.put_throttle = int(arg[len("-putthrottle:"):])
        elif arg.startswith('-pt:'):
            config.put_throttle = int(arg[len("-pt:"):])
        elif arg == '-log':
            if moduleName not in config.log:
                config.log.append(moduleName)
        elif arg.startswith('-log:'):
            if moduleName not in config.log:
                config.log.append(moduleName)
            config.logfilename = arg[len("-log:"):]
        elif arg == '-nolog':
            if moduleName in config.log:
                config.log.remove(moduleName)
        elif arg in ('-cosmeticchanges', '-cc'):
            config.cosmetic_changes = not config.cosmetic_changes
            output(u'NOTE: option cosmetic_changes is %s\n'
                   % config.cosmetic_changes)
        elif arg == '-simulate':
            config.simulate = True
        #
        #  DEBUG control:
        #
        #    The framework has four layers (by default, others can be added),
        #    each designated by a string --
        #
        #    1.  "comm": the communication layer (http requests, etc.)
        #    2.  "data": the raw data layer (API requests, XML dump parsing)
        #    3.  "wiki": the wiki content representation layer (Page and Site
        #         objects)
        #    4.  "bot": the application layer (user scripts should always
        #         send any debug() messages to this layer)
        #
        #    The "-debug:layer" flag sets the logger for any specified
        #    layer to the DEBUG level, causing it to output extensive debugging
        #    information. Otherwise, the default logging setting is the INFO
        #    level. "-debug" with no layer specified sets _all_ loggers to
        #    DEBUG level.
        #
        #    This method does not check the 'layer' part of the flag for
        #    validity.
        #
        #    If used, "-debug" turns on file logging, regardless of any
        #    other settings.
        #
        elif arg == '-debug':
            if moduleName not in config.log:
                config.log.append(moduleName)
            if "" not in config.debug_log:
                config.debug_log.append("")
        elif arg.startswith("-debug:"):
            if moduleName not in config.log:
                config.log.append(moduleName)
            component = arg[len("-debug:"):]
            if component not in config.debug_log:
                config.debug_log.append(component)
        elif arg in ('-verbose', '-v'):
            config.verbose_output += 1
        elif arg.startswith('-daemonize'):
            redirect_std = arg[len('-daemonize:'):] if ':' in arg else None
            daemonize.daemonize(redirect_std=redirect_std)
        else:
            # the argument depends on numerical config settings
            # e.g. -maxlag:
            try:
                _arg, _val = arg[1:].split(':')
                # explicitly check for int (so bool doesn't match)
                if not isinstance(getattr(config, _arg), int):
                    raise TypeError
                setattr(config, _arg, int(_val))
            except (ValueError, TypeError, AttributeError):
                # argument not global -> specific bot script will take care
                nonGlobalArgs.append(arg)

    if username:
        config.usernames[config.family][config.mylang] = username

    init_handlers()
    writeToCommandLogFile()

    if config.verbose_output:
        # Please don't change the regular expression here unless you really
        # have to - some git versions (like 1.7.0.4) seem to treat lines
        # containing just `$Id:` as if they were ident lines (see
        # gitattributes(5)) leading to unwanted behaviour like automatic
        # replacement with `$Id: feaa3d5786f5b4cad37e58f6158372483304b875 $`
        # or `$Id: feaa3d5786f5b4cad37e58f6158372483304b875 $`.
        m = re.search(r"\$Id"
                      r": (\w+) \$", pywikibot.__version__)
        if m:
            pywikibot.output(u'Pywikibot r%s' % m.group(1))
        else:
            # Version ID not available on SVN repository.
            # Maybe this information should be imported from version.py
            pywikibot.output(u'Pywikibot SVN repository')
        pywikibot.output(u'Python %s' % sys.version)

    if do_help:
        showHelp()
        sys.exit(0)

    pywikibot.debug(u"handle_args() completed.", _logger)
    return nonGlobalArgs


@deprecated("handle_args")
def handleArgs(*args):
    """DEPRECATED. Use handle_args()."""
    return handle_args(args)


def showHelp(module_name=None):
    """Show help for the Bot."""
    if not module_name:
        module_name = calledModuleName()
    if not module_name:
        try:
            module_name = sys.modules['__main__'].main.__module__
        except NameError:
            module_name = "no_module"

    globalHelp = u'''
Global arguments available for all bots:

-dir:PATH         Read the bot's configuration data from directory given by
                  PATH, instead of from the default directory.

-lang:xx          Set the language of the wiki you want to work on, overriding
                  the configuration in user-config.py. xx should be the
                  language code.

-family:xyz       Set the family of the wiki you want to work on, e.g.
                  wikipedia, wiktionary, wikitravel, ...
                  This will override the configuration in user-config.py.

-user:xyz         Log in as user 'xyz' instead of the default username.

-daemonize:xyz    Immediately return control to the terminal and redirect
                  stdout and stderr to file xyz.
                  (only use for bots that require no input from stdin).

-help             Show this help text.

-log              Enable the log file, using the default filename
                  '%s-bot.log'
                  Logs will be stored in the logs subdirectory.

-log:xyz          Enable the log file, using 'xyz' as the filename.

-nolog            Disable the log file (if it is enabled by default).

-maxlag           Sets a new maxlag parameter to a number of seconds. Defer bot
                  edits during periods of database server lag. Default is set by
                  config.py

-putthrottle:n    Set the minimum time (in seconds) the bot will wait between
-pt:n             saving pages.
-put_throttle:n

-debug:item       Enable the log file and include extensive debugging data
-debug            for component "item" (for all components if the second form
                  is used).

-verbose          Have the bot provide additional console output that may be
-v                useful in debugging.

-cosmeticchanges  Toggles the cosmetic_changes setting made in config.py or
-cc               user_config.py to its inverse and overrules it. All other
                  settings and restrictions are untouched.

-simulate         Disables writing to the server. Useful for testing and
                  debugging of new code (if given, doesn't do any real
                  changes, but only shows what would have been changed).

-<config var>:n   You may use all given numeric config variables as option and
                  modify it with command line.

''' % module_name
    try:
        module = __import__('%s' % module_name)
        helpText = module.__doc__
        if sys.version_info[0] < 3 and isinstance(helpText, str):
            helpText = helpText.decode('utf-8')
        if hasattr(module, 'docuReplacements'):
            for key, value in module.docuReplacements.items():
                helpText = helpText.replace(key, value.strip('\n\r'))
        pywikibot.stdout(helpText)  # output to STDOUT
    except Exception:
        if module_name:
            pywikibot.stdout(u'Sorry, no help available for %s' % module_name)
        pywikibot.log('showHelp:', exc_info=True)
    pywikibot.stdout(globalHelp)


def writeToCommandLogFile():
    """
    Save name of the called module along with all parameters to logs/commands.log.

    This can be used by user later to track errors or report bugs.
    """
    modname = calledModuleName()
    # put quotation marks around all parameters
    args = [modname] + [u'"%s"' % s for s in pywikibot.argvu[1:]]
    command_log_filename = config.datafilepath('logs', 'commands.log')
    try:
        command_log_file = codecs.open(command_log_filename, 'a', 'utf-8')
    except IOError:
        command_log_file = codecs.open(command_log_filename, 'w', 'utf-8')
    # add a timestamp in ISO 8601 formulation
    isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    command_log_file.write('%s r%s Python %s '
                           % (isoDate, version.getversiondict()['rev'],
                              sys.version.split()[0]))
    s = u' '.join(args)
    command_log_file.write(s + os.linesep)
    command_log_file.close()


def open_webbrowser(page):
    """Open the web browser displaying the page and wait for input."""
    from pywikibot import i18n
    webbrowser.open(page.full_url())
    i18n.input('pywikibot-enter-finished-browser')


class QuitKeyboardInterrupt(KeyboardInterrupt):

    """The user has cancelled processing at a prompt."""


class Bot(object):

    """
    Generic Bot to be subclassed.

    This class provides a run() method for basic processing of a
    generator one page at a time.

    If the subclass places a page generator in self.generator,
    Bot will process each page in the generator, invoking the method treat()
    which must then be implemented by subclasses.

    If the subclass does not set a generator, or does not override
    treat() or run(), NotImplementedError is raised.
    """

    # Bot configuration.
    # Only the keys of the dict can be passed as init options
    # The values are the default values
    # Extend this in subclasses!
    availableOptions = {
        'always': False,  # ask for confirmation when putting a page?
    }

    _current_page = None

    def __init__(self, **kwargs):
        """
        Only accept options defined in availableOptions.

        @param kwargs: bot options
        @type kwargs: dict
        """
        if 'generator' in kwargs:
            self.generator = kwargs.pop('generator')

        # TODO: add warning if site is specified and generator
        # contains pages from a different site.
        self._site = kwargs.pop('site', None)
        self._sites = set([self._site] if self._site else [])

        self.setOptions(**kwargs)

        self._treat_counter = 0
        self._save_counter = 0

    def setOptions(self, **kwargs):
        """
        Set the instance options.

        @param kwargs: options
        @type kwargs: dict
        """
        # contains the options overridden from defaults
        self.options = {}

        validOptions = set(self.availableOptions)
        receivedOptions = set(kwargs)

        for opt in receivedOptions & validOptions:
            self.options[opt] = kwargs[opt]

        for opt in receivedOptions - validOptions:
            pywikibot.warning(u'%s is not a valid option. It was ignored.'
                              % opt)

    def getOption(self, option):
        """
        Get the current value of an option.

        @param option: key defined in Bot.availableOptions
        """
        try:
            return self.options.get(option, self.availableOptions[option])
        except KeyError:
            raise pywikibot.Error(u'%s is not a valid bot option.' % option)

    @property
    def current_page(self):
        """Return the current working page as a property."""
        return self._current_page

    @current_page.setter
    def current_page(self, page):
        """Set the current working page as a property.

        When the value is actually changed, the page title is printed
        to the standard output (highlighted in purple) and logged
        with a VERBOSE level.

        This also prevents the same title from being printed twice.

        @param page: the working page
        @type  page: pywikibot.Page
        """
        if page != self._current_page:
            self._current_page = page
            msg = u'Working on %r' % page.title()
            if config.colorized_output:
                log(msg)
                stdout(u'\n\n>>> \03{lightpurple}%s\03{default} <<<'
                       % page.title())
            else:
                stdout(msg)

    def user_confirm(self, question):
        """Obtain user response if bot option 'always' not enabled."""
        if self.getOption('always'):
            return True

        choice = pywikibot.input_choice(question,
                                        [('Yes', 'y'),
                                         ('No', 'N'),
                                         ('All', 'a')],
                                        default='N')

        if choice == 'n':
            return False

        if choice == 'q':
            self.quit()

        if choice == 'a':
            # Remember the choice
            self.options['always'] = True

        return True

    @deprecated_args(comment='summary')
    def userPut(self, page, oldtext, newtext, **kwargs):
        """
        Save a new revision of a page, with user confirmation as required.

        Print differences, ask user for confirmation,
        and puts the page if needed.

        Option used:
        * 'always'

        Keyword args used:
        * 'async' - passed to page.save
        * 'summary' - passed to page.save
        * 'show_diff' - show changes between oldtext and newtext (enabled)
        * 'ignore_save_related_errors' - report and ignore (disabled)
        * 'ignore_server_errors' - report and ignore (disabled)
        """
        if oldtext == newtext:
            pywikibot.output(u'No changes were needed on %s'
                             % page.title(asLink=True))
            return

        self.current_page = page

        show_diff = kwargs.pop('show_diff', True)

        if show_diff:
            pywikibot.showDiff(oldtext, newtext)

        if 'summary' in kwargs:
            pywikibot.output(u'Edit summary: %s' % kwargs['summary'])

        page.text = newtext
        self._save_page(page, page.save, **kwargs)

    def _save_page(self, page, func, *args, **kwargs):
        """
        Helper function to handle page save-related option error handling.

        @param page: currently edited page
        @param func: the function to call
        @param args: passed to the function
        @param kwargs: passed to the function
        @kwarg ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        @kwtype ignore_server_errors: bool
        @kwarg ignore_save_related_errors: if True, errors related to
        page save will be reported and ignored (default: False)
        @kwtype ignore_save_related_errors: bool
        """
        if not self.user_confirm('Do you want to accept these changes?'):
            return

        if 'async' not in kwargs and self.getOption('always'):
            kwargs['async'] = True

        ignore_save_related_errors = kwargs.pop('ignore_save_related_errors',
                                                False)
        ignore_server_errors = kwargs.pop('ignore_server_errors', False)

        try:
            func(*args, **kwargs)
            self._save_counter += 1
        except pywikibot.PageSaveRelatedError as e:
            if not ignore_save_related_errors:
                raise
            if isinstance(e, pywikibot.EditConflict):
                pywikibot.output(u'Skipping %s because of edit conflict'
                                 % page.title())
            elif isinstance(e, pywikibot.SpamfilterError):
                pywikibot.output(
                    u'Cannot change %s because of blacklist entry %s'
                    % (page.title(), e.url))
            elif isinstance(e, pywikibot.LockedPage):
                pywikibot.output(u'Skipping %s (locked page)'
                                 % page.title())
            else:
                pywikibot.error(
                    u'Skipping %s because of a save related error: %s'
                    % (page.title(), e))
        except pywikibot.ServerError as e:
            if not ignore_server_errors:
                raise
            pywikibot.error(u'Server Error while processing %s: %s'
                            % (page.title(), e))

    def quit(self):
        """Cleanup and quit processing."""
        raise QuitKeyboardInterrupt

    def treat(self, page):
        """Process one page (Abstract method)."""
        raise NotImplementedError('Method %s.treat() not implemented.'
                                  % self.__class__.__name__)

    @property
    def site(self):
        """Site that the bot is using."""
        if not self._site:
            warning('Bot.site was not set before being retrieved.')
            # TODO: peak at a page from the generator to determine the site
            self.site = pywikibot.Site()
            warning('Using the default site: %s' % self.site)
        return self._site

    @site.setter
    def site(self, site):
        """
        Set the Site that the bot is using.

        When Bot.run() is managing the generator and site property, this is
        set each time a page is on a site different from the previous page.
        """
        if not site:
            self._site = None
            return

        if site not in self._sites:
            log(u'LOADING SITE %s VERSION: %s'
                % (site, site.version()))

            self._sites.add(site)
            if len(self._sites) == 2:
                log('%s uses multiple sites' % self.__class__.__name__)
        if self._site and self._site != site:
            log('%s: changing site from %s to %s'
                % (self.__class__.__name__, self._site, site))
        self._site = site

    def run(self):
        """Process all pages in generator."""
        if not hasattr(self, 'generator'):
            raise NotImplementedError('Variable %s.generator not set.'
                                      % self.__class__.__name__)

        # This check is to remove the possibility that the superclass changing
        # self.site causes bugs in subclasses.
        # If the subclass has set self.site before run(), it may be that the
        # bot processes pages on sites other than self.site, and therefore
        # this method cant alter self.site.  To use this functionality, don't
        # set self.site in __init__, and use page.site in treat().
        auto_update_site = not self._site
        if not auto_update_site:
            warning(
                '%s.__init__ set the Bot.site property; this is only needed '
                'when the Bot accesses many sites.' % self.__class__.__name__)
        else:
            log('Bot is managing the %s.site property in run()'
                % self.__class__.__name__)

        maxint = 0
        if sys.version_info[0] == 2:
            maxint = sys.maxint

        try:
            for page in self.generator:
                # When in auto update mode, set the site when it changes,
                # so subclasses can hook onto changes to site.
                if (auto_update_site and
                        (not self._site or page.site != self.site)):
                    self.site = page.site

                # Process the page
                self.treat(page)

                self._treat_counter += 1
                if maxint and self._treat_counter == maxint:
                    # Warn the user that the bot may not function correctly
                    pywikibot.error(
                        '\n%s: page count reached Python 2 sys.maxint (%d).\n'
                        'Python 3 should be used to process very large batches'
                        % (self.__class__.__name__, sys.maxint))
        except QuitKeyboardInterrupt:
            pywikibot.output('\nUser quit %s bot run...' %
                             self.__class__.__name__)
        except KeyboardInterrupt:
            if config.verbose_output:
                raise
            else:
                pywikibot.output('\nKeyboardInterrupt during %s bot run...' %
                                 self.__class__.__name__)


class CurrentPageBot(Bot):

    """A bot which automatically sets 'current_page' on each treat()."""

    ignore_save_related_errors = True
    ignore_server_errors = False

    def treat_page(self):
        """Process one page (Abstract method)."""
        raise NotImplementedError('Method %s.treat_page() not implemented.'
                                  % self.__class__.__name__)

    def treat(self, page):
        """Set page to current page and treat that page."""
        self.current_page = page
        self.treat_page()

    @deprecated_args(comment='summary')
    def put_current(self, new_text, ignore_save_related_errors=None,
                    ignore_server_errors=None, **kwargs):
        """
        Call L{Bot.userPut} but use the current page.

        It compares the new_text to the current page text.

        @param new_text: The new text
        @type new_text: basestring
        @param ignore_save_related_errors: Ignore save related errors and
            automatically print a message. If None uses this instances default.
        @type ignore_save_related_errors: bool or None
        @param ignore_server_errors: Ignore server errors and automatically
            print a message. If None uses this instances default.
        @type ignore_server_errors: bool or None
        @param kwargs: Additional parameters directly given to L{Bot.userPut}.
        @type kwargs: dict
        """
        if ignore_save_related_errors is None:
            ignore_save_related_errors = self.ignore_save_related_errors
        if ignore_server_errors is None:
            ignore_server_errors = self.ignore_server_errors
        self.userPut(self.current_page, self.current_page.text, new_text,
                     ignore_save_related_errors=ignore_save_related_errors,
                     ignore_server_errors=ignore_server_errors,
                     **kwargs)


class ExistingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats existing pages."""

    def treat(self, page):
        """Treat page if it exists and handle NoPage from it."""
        if not page.exists():
            pywikibot.warning('Page "{0}" does not exist on {1}.'.format(
                page.title(), page.site))
            return
        try:
            super(ExistingPageBot, self).treat(page)
        except pywikibot.NoPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a NoPage exception was '
                'raised.'.format(page.title(), page.site))


class FollowRedirectPageBot(CurrentPageBot):

    """A CurrentPageBot class which follows the redirect."""

    def treat(self, page):
        """Treat target if page is redirect and the page otherwise."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        super(FollowRedirectPageBot, self).treat(page)


class CreatingPageBot(CurrentPageBot):

    """A CurrentPageBot class which only treats nonexistent pages."""

    def treat(self, page):
        """Treat page if doesn't exist."""
        if page.exists():
            pywikibot.warning('Page "{0}" does already exist on {1}.'.format(
                page.title(), page.site))
            return
        super(CreatingPageBot, self).treat(page)


class RedirectPageBot(CurrentPageBot):

    """A RedirectPageBot class which only treats redirects."""

    def treat(self, page):
        """Treat only redirect pages and handle IsNotRedirectPage from it."""
        if not page.isRedirectPage():
            pywikibot.warning('Page "{0}" on {1} is skipped because it is not '
                              'a redirect'.format(page.title(), page.site))
            return
        try:
            super(RedirectPageBot, self).treat(page)
        except pywikibot.IsNotRedirectPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a IsNotRedirectPage '
                'exception was raised.'.format(page.title(), page.site))


class NoRedirectPageBot(CurrentPageBot):

    """A NoRedirectPageBot class which only treats non-redirects."""

    def treat(self, page):
        """Treat only non-redirect pages and handle IsRedirectPage from it."""
        if page.isRedirectPage():
            pywikibot.warning('Page "{0}" on {1} is skipped because it is a '
                              'redirect'.format(page.title(), page.site))
            return
        try:
            super(NoRedirectPageBot, self).treat(page)
        except pywikibot.IsRedirectPage as e:
            if e.page != page:
                raise
            pywikibot.warning(
                'During handling of page "{0}" on {1} a IsRedirectPage '
                'exception was raised.'.format(page.title(), page.site))


class WikidataBot(Bot):

    """
    Generic Wikidata Bot to be subclassed.

    Source claims (P143) can be created for specific sites.
    """

    def __init__(self, **kwargs):
        """
        Constructor of the WikidataBot.

        @kwarg use_from_page: If True (default) it will apply ItemPage.fromPage
            for every item. If False it assumes that the pages are actually
            already ItemPage (page in treat will be None). If None it'll use
            ItemPage.fromPage when the page is not in the site's item
            namespace.
        @kwtype use_from_page: bool, None
        """
        self.use_from_page = kwargs.pop('use_from_page', True)
        super(WikidataBot, self).__init__(**kwargs)
        self.site = pywikibot.Site()
        self.repo = self.site.data_repository()
        if self.repo is None:
            raise pywikibot.exceptions.WikiBaseError(
                '%s is not connected to a data repository' % self.site)

    def cacheSources(self):
        """
        Fetch the sources from the list on Wikidata.

        It is stored internally and reused by getSource()
        """
        page = pywikibot.Page(self.repo, u'List of wikis/python', ns=4)
        self.source_values = json.loads(page.get())
        for family_code, family in self.source_values.items():
            for source_lang in family:
                self.source_values[family_code][source_lang] = pywikibot.ItemPage(self.repo,
                                                                                  family[source_lang])

    def get_property_by_name(self, property_name):
        """
        Find given property and return its ID.

        Method first uses site.search() and if the property isn't found, then
        asks user to provide the property ID.

        @param property_name: property to find
        @type property_name: str
        """
        ns = self.site.data_repository().property_namespace
        for page in self.site.search(property_name, step=1, total=1,
                                     namespaces=ns):
            page = pywikibot.PropertyPage(self.site.data_repository(),
                                          page.title())
            pywikibot.output(u"Assuming that %s property is %s." %
                             (property_name, page.id))
            return page.id
        return pywikibot.input(u'Property %s was not found. Please enter the '
                               u'property ID (e.g. P123) of it:'
                               % property_name).upper()

    def user_edit_entity(self, item, data=None, **kwargs):
        """
        Edit entity with data provided, with user confirmation as required.

        @param item: page to be edited
        @type item: ItemPage
        @param data: data to be saved, or None if the diff should be created
          automatically
        @kwarg summary: revision comment, passed to ItemPage.editEntity
        @kwtype summary: str
        @kwarg show_diff: show changes between oldtext and newtext (default:
          True)
        @kwtype show_diff: bool
        @kwarg ignore_server_errors: if True, server errors will be reported
          and ignored (default: False)
        @kwtype ignore_server_errors: bool
        @kwarg ignore_save_related_errors: if True, errors related to
        page save will be reported and ignored (default: False)
        @kwtype ignore_save_related_errors: bool
        """
        self.current_page = item

        show_diff = kwargs.pop('show_diff', True)
        if show_diff:
            if data is None:
                diff = item.toJSON(diffto=(
                    item._content if hasattr(item, '_content') else None))
            else:
                diff = pywikibot.WikibasePage._normalizeData(data)
            pywikibot.output(json.dumps(diff, indent=4, sort_keys=True))

        if 'summary' in kwargs:
            pywikibot.output(u'Change summary: %s' % kwargs['summary'])

        # TODO async in editEntity should actually have some effect (bug T86074)
        # TODO PageSaveRelatedErrors should be actually raised in editEntity
        # (bug T86083)
        self._save_page(item, item.editEntity, data, **kwargs)

    def getSource(self, site):
        """
        Create a Claim usable as a source for Wikibase statements.

        @param site: site that is the source of assertions.
        @type site: Site

        @return: Claim
        """
        if site.family.name in self.source_values and site.code in self.source_values[site.family.name]:
            source = pywikibot.Claim(self.repo, 'P143')
            source.setTarget(self.source_values.get(site.family.name).get(site.code))
            return source

    def run(self):
        """Process all pages in generator."""
        if not hasattr(self, 'generator'):
            raise NotImplementedError('Variable %s.generator not set.'
                                      % self.__class__.__name__)

        treat_missing_item = hasattr(self, 'treat_missing_item')

        try:
            for page in self.generator:
                if not page.exists():
                    pywikibot.output('%s doesn\'t exist.' % page)
                # FIXME: Hack because 'is_data_repository' doesn't work if
                #        site is the APISite. See T85483
                data_site = page.site.data_repository()
                if (data_site.family == page.site.family and
                        data_site.code == page.site.code):
                    is_item = page.namespace() == data_site.item_namespace.id
                else:
                    is_item = False
                if self.use_from_page is not True and is_item:
                    item = pywikibot.ItemPage(data_site, page.title())
                    item.get()
                elif self.use_from_page is False:
                    pywikibot.error('{0} is not in the item namespace but '
                                    'must be an item.'.format(page))
                    continue
                else:
                    try:
                        item = pywikibot.ItemPage.fromPage(page)
                    except pywikibot.NoPage:
                        item = None
                if not item:
                    if not treat_missing_item:
                        pywikibot.output(
                            '%s doesn\'t have a wikidata item.' % page)
                        # TODO: Add an option to create the item
                        continue
                self.treat(page, item)
        except QuitKeyboardInterrupt:
            pywikibot.output('\nUser quit %s bot run...' %
                             self.__class__.__name__)
        except KeyboardInterrupt:
            if config.verbose_output:
                raise
            else:
                pywikibot.output('\nKeyboardInterrupt during %s bot run...' %
                                 self.__class__.__name__)
        except Exception as e:
                pywikibot.exception(msg=e, tb=True)
