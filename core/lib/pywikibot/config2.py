# -*- coding: utf-8 -*-
"""
Module to define and load pywikibot configuration default and user preferences.

User preferences are loaded from a python file called user-config.py, which
may be located in directory specified by the environment variable
PYWIKIBOT2_DIR, or the same directory as pwb.py, or in a directory within
the users home.  See get_base_dir for more information.

If user-config.py can not be found in any of those locations, this module
will fail to load unless the environment variable PYWIKIBOT2_NO_USER_CONFIG
is set to a value other than '0'.  i.e. PYWIKIBOT2_NO_USER_CONFIG=1 will
allow config to load without a user-config.py.  However, warnings will be
shown if user-config.py was not loaded.
To prevent these warnings, set PYWIKIBOT2_NO_USER_CONFIG=2.

Provides two functions to register family classes which can be used in
the user-config:

 - register_family_file
 - register_families_folder

Other functions made available to user-config:

 - user_home_path

Sets module global base_dir and provides utility methods to
build paths relative to base_dir:

 - makepath
 - datafilepath
 - shortpath
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id: 731ed8a4832c79462c423c12f22828f18f6ea065 $'
#

import collections
import os
import stat
import sys

from warnings import warn

if sys.platform == 'win32':
    if sys.version_info[0] > 2:
        import winreg
    else:
        import _winreg as winreg

# This frozen set should contain all imported modules/variables, so it must
# occur directly after the imports. At that point globals() only contains the
# names and some magic variables (like __name__)
_imports = frozenset(name for name in globals() if not name.startswith('_'))

__no_user_config = os.environ.get('PYWIKIBOT2_NO_USER_CONFIG')
if __no_user_config == '0':
    __no_user_config = None


class _ConfigurationDeprecationWarning(UserWarning):

    """Feature that is no longer supported."""

    pass

# IMPORTANT:
# Do not change any of the variables in this file. Instead, make
# a file user-config.py, and overwrite values in there.

# Note: all variables defined in this module are made available to bots as
# configuration settings, *except* variable names beginning with an
# underscore (example: _variable).  Be sure to use an underscore on any
# variables that are intended only for internal use and not to be exported
# to other modules.

_private_values = ['authenticate', 'proxy', 'db_password']
_deprecated_variables = ['use_SSL_onlogin', 'use_SSL_always',
                         'available_ssl_project']

# ############# ACCOUNT SETTINGS ##############

# The family of sites we are working on. pywikibot will import
# families/xxx_family.py so if you want to change this variable,
# you need to write such a file if one does not exist.
family = 'wikipedia'
# The language code of the site we're working on.
mylang = 'language'
# If family and mylang are not modified from the above, the default is changed
# to test:test, which is test.wikipedia.org, at the end of this module.

# The dictionary usernames should contain a username for each site where you
# have a bot account. Please set your usernames by adding such lines to your
# user-config.py:
#
# usernames['wikipedia']['de'] = 'myGermanUsername'
# usernames['wiktionary']['en'] = 'myEnglishUsername'
#
# If you have a unique username for all languages of a family,
# you can use '*'
# usernames['wikibooks']['*'] = 'mySingleUsername'
#
# If you have a sysop account on some wikis, this will be used to delete pages
# or to edit locked pages if you add such lines to your
# user-config.py:
#
# sysopnames['wikipedia']['de'] = 'myGermanUsername'
# sysopnames['wiktionary']['en'] = 'myEnglishUsername'
#
# If you have a unique syop account for all languages of a family,
# you can use '*'
# sysopnames['myownwiki']['*'] = 'mySingleUsername'
usernames = collections.defaultdict(dict)
sysopnames = collections.defaultdict(dict)
disambiguation_comment = collections.defaultdict(dict)

# User agent format.
# For the meaning and more help in customization see:
# https://www.mediawiki.org/wiki/Manual:Pywikibot/User-agent
user_agent_format = '{script_product} ({script_comments}) {pwb} ({revision}) {httplib2} {python}'

# The default interface for communicating with the site
# currently the only defined interface is 'APISite', so don't change this!
site_interface = 'APISite'
# number of days to cache namespaces, api configuration, etc.
API_config_expiry = 30

# The maximum number of bytes which uses a GET request, if not positive
# it'll always use POST requests
maximum_GET_length = 255
# Some networks modify GET requests when they are not encrypted, to avoid
# bug reports related to that disable those. If we are confident that bug
# related to this are really because of the network this could be changed.
enable_GET_without_SSL = False

# Solve captchas in the webbrowser. Setting this to False will result in the
# exception CaptchaError being thrown if a captcha is encountered.
solve_captcha = True

# Some sites will require password authentication to access the HTML pages at
# the site. If you have any such site, add lines to your user-config.py of
# the following form:
#
# authenticate['en.wikipedia.org'] = ('John','XXXXX')
#
# where John is your login name, and XXXXX your password.
# Note:
# 1. This is only for sites that use authentication in the form that gives
#    you a popup for name and password when you try to access any data, NOT
#    for, for example, wiki usernames
# 2. You must use the hostname of the site, not its family/language pair
authenticate = {}

#
# Secure connection overrides
#
# These settings are deprecated.  They existed to support the Wikimedia
# family which only served HTTPS on https://secure.wikimedia.org/<site>/<uri>
# Use Family.protocol()
use_SSL_onlogin = False  # if available, use SSL when logging in
use_SSL_always = False   # if available, use SSL for all API queries
# Available secure projects should be listed here.
available_ssl_project = []

# By default you are asked for a password on the terminal.
# A password file may be used. e.g. password_file = ".passwd"
# The password file should consist of lines containing
# Python tuples of any of the following formats:
# (code, family, username, password)
# (family, username, password)
# (username, password)
password_file = None

# edit summary to use if not supplied by bot script
# WARNING: this should NEVER be used in practice, ALWAYS supply a more
#          relevant summary for bot edits
default_edit_summary = u'Pywikibot v.2'

# What permissions to use to set private files to it
# such as password file.
#
# stat.S_IRWXU 0o700 mask for owner permissions
# stat.S_IRUSR 0o400 read permission for owner
# stat.S_IWUSR 0o200 write permission for owner
# stat.S_IXUSR 0o100 execute permission for owner
# stat.S_IRWXG 0o070 mask for group permissions
# stat.S_IRGRP 0o040 read permission for group
# stat.S_IWGRP 0o020 write permission for group
# stat.S_IXGRP 0o010 execute permission for group
# stat.S_IRWXO 0o007 mask for others permissions
# stat.S_IROTH 0o004 read permission for others
# stat.S_IWOTH 0o002 write permission for others
# stat.S_IXOTH 0o001 execute permission for others
private_files_permission = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR

# Allow user to stop warnings about file security
# by setting this to true.
ignore_file_security_warnings = False


def user_home_path(path):
    """Return a file path to a file in the user home."""
    return os.path.join(os.path.expanduser('~'), path)


def get_base_dir(test_directory=None):
    r"""Return the directory in which user-specific information is stored.

    This is determined in the following order:
     1.  If the script was called with a -dir: argument, use the directory
         provided in this argument.
     2.  If the user has a PYWIKIBOT2_DIR environment variable, use the value
         of it.
     3.  If user-config is present in current directory, use the current
         directory.
     4.  If user-config is present in pwb.py directory, use that directory
     5.  Use (and if necessary create) a 'pywikibot' folder under
         'Application Data' or 'AppData\Roaming' (Windows) or
         '.pywikibot' directory (Unix and similar) under the user's home
         directory.

    Set PYWIKIBOT2_NO_USER_CONFIG=1 to disable loading user-config.py

    @param test_directory: Assume that a user config file exists in this
        directory. Used to test whether placing a user config file in this
        directory will cause it to be selected as the base directory.
    @type test_directory: str or None
    @rtype: unicode
    """
    def exists(directory):
        directory = os.path.abspath(directory)
        if directory == test_directory:
            return True
        else:
            return os.path.exists(os.path.join(directory, 'user-config.py'))

    if test_directory is not None:
        test_directory = os.path.abspath(test_directory)

    DIRNAME_WIN = u"Pywikibot"
    DIRNAME_WIN_FBCK = u"pywikibot"
    DIRNAME_UNIX = u".pywikibot"

    base_dir = ""
    for arg in sys.argv[1:]:
        if arg.startswith(str('-dir:')):
            base_dir = arg[5:]
            base_dir = os.path.expanduser(base_dir)
            break
    else:
        if ('PYWIKIBOT2_DIR' in os.environ and
                exists(os.path.abspath(os.environ['PYWIKIBOT2_DIR']))):
            base_dir = os.path.abspath(os.environ['PYWIKIBOT2_DIR'])
        elif exists('.'):
            base_dir = os.path.abspath('.')
        elif ('PYWIKIBOT2_DIR_PWB' in os.environ and
                exists(os.path.abspath(os.environ['PYWIKIBOT2_DIR_PWB']))):
            base_dir = os.path.abspath(os.environ['PYWIKIBOT2_DIR_PWB'])
        else:
            base_dir_cand = []
            home = os.path.expanduser("~")
            if sys.platform == 'win32':
                import platform
                win_version = int(platform.version().split(".")[0])
                if win_version == 5:
                    sub_dir = ["Application Data"]
                elif win_version in (6, 10):
                    sub_dir = ["AppData", "Roaming"]
                else:
                    raise WindowsError(u'Windows version %s not supported yet.'
                                       % win_version)
                base_dir_cand.extend([[home] + sub_dir + [DIRNAME_WIN],
                                     [home] + sub_dir + [DIRNAME_WIN_FBCK]])
            else:
                base_dir_cand.append([home, DIRNAME_UNIX])

            for dir in base_dir_cand:
                dir = os.path.join(*dir)
                if not os.path.isdir(dir):
                    os.makedirs(dir, mode=private_files_permission)
                if exists(dir):
                    base_dir = dir
                    break

    if not os.path.isabs(base_dir):
        base_dir = os.path.normpath(os.path.join(os.getcwd(), base_dir))
    # make sure this path is valid and that it contains user-config file
    if not os.path.isdir(base_dir):
        raise RuntimeError("Directory '%s' does not exist." % base_dir)
    # check if user-config.py is in base_dir
    if not exists(base_dir):
        exc_text = "No user-config.py found in directory '%s'.\n" % base_dir
        if __no_user_config:
            if __no_user_config != '2':
                print(exc_text)
        else:
            exc_text += "  Please check that user-config.py is stored in the correct location.\n"
            exc_text += "  Directory where user-config.py is searched is determined as follows:\n\n"
            exc_text += "    " + get_base_dir.__doc__
            raise RuntimeError(exc_text)

    return base_dir

_get_base_dir = get_base_dir  # for backward compatibility
_base_dir = get_base_dir()
# Save base_dir for use by other modules
base_dir = _base_dir

for arg in sys.argv[1:]:
    if arg.startswith(str('-verbose')) or arg == str('-v'):
        print("The base directory is %s" % base_dir)
        break
family_files = {}


def register_family_file(family_name, file_path):
    """Register a single family class file."""
    usernames[family_name] = {}
    sysopnames[family_name] = {}
    disambiguation_comment[family_name] = {}
    family_files[family_name] = file_path


def register_families_folder(folder_path):
    """Register all family class files contained in a directory."""
    for file_name in os.listdir(folder_path):
        if file_name.endswith("_family.py"):
            family_name = file_name[:-len("_family.py")]
            register_family_file(family_name, os.path.join(folder_path, file_name))


# Get the names of all known families, and initialize with empty dictionaries.
# ‘families/’ is a subdirectory of the directory in which config2.py is found.
register_families_folder(os.path.join(os.path.dirname(__file__), 'families'))
register_family_file('wikiapiary', 'https://wikiapiary.com')

# Set to True to override the {{bots}} exclusion protocol (at your own risk!)
ignore_bot_templates = False

# ############# USER INTERFACE SETTINGS ##############

# The encoding that's used in the user's console, i.e. how strings are encoded
# when they are read by raw_input(). On Windows systems' DOS box, this should
# be 'cp850' ('cp437' for older versions). Linux users might try 'iso-8859-1'
# or 'utf-8'.
# This default code should work fine, so you don't have to think about it.
# TODO: consider getting rid of this config variable.
try:
    if sys.version_info[0] > 2 or not sys.stdout.encoding:
        console_encoding = sys.stdout.encoding
    else:
        console_encoding = sys.stdout.encoding.decode('ascii')
except:
    # When using pywikibot inside a daemonized twisted application,
    # we get "StdioOnnaStick instance has no attribute 'encoding'"
    console_encoding = None

# The encoding the user would like to see text transliterated to. This can be
# set to a charset (e.g. 'ascii', 'iso-8859-1' or 'cp850'), and we will output
# only characters that exist in that charset. However, the characters will be
# output using console_encoding.
# If this is not defined on Windows, we emit a Warning explaining the user
# to either switch to a Unicode-able font and use
#    transliteration_target = None
# or to keep using raster fonts and set
#    transliteration_target = console_encoding
# After emitting the warning, this last option will be set.

transliteration_target = None

# The encoding in which textfiles are stored, which contain lists of page
# titles. The most used is: 'utf-8'. 'utf-8-sig' recognizes BOM but it is
# available on Python 2.5 or higher. For a complete list please see:
# https://docs.python.org/2/library/codecs.html#standard-encodings
textfile_encoding = 'utf-8'

# tkinter isn't yet ready
userinterface = 'terminal'

# this can be used to pass variables to the UI init function
# useful for e.g.
# userinterface_init_kwargs = {'default_stream': 'stdout'}
userinterface_init_kwargs = {}

# i18n setting for user interface language
# default is obtained from L{locale.getdefaultlocale}
userinterface_lang = None

# Should we transliterate characters that do not exist in the console
# character set?
# True: whenever possible
# False: never - always replace them by question marks
# Currently only works if interface 'terminal' is set.
transliterate = True

# Should the system bell ring if the bot expects user input?
ring_bell = False

# Colorization can be used to markup important text parts of the output.
# On Linux/Unix terminals, ANSI escape codes are used for this. On Windows,
# it is done by a DLL call via ctypes. ctypes is only available since
# Python 2.5, so if you're using Python 2.4 or lower on Windows, you should
# upgrade.
# Set this to False if you're using Linux and your tty doesn't support
# ANSI colors.
try:
    # Don't print colorized when the output is, for example, piped to a file.
    colorized_output = sys.stdout.isatty()
except:
    colorized_output = False

# An indication of the size of your screen, or rather the size of the screen
# to be shown, for flickrripper
tkhorsize = 1600
tkvertsize = 1000

# ############# EXTERNAL EDITOR SETTINGS ##############
# The command for the editor you want to use. If set to None, a simple Tkinter
# editor will be used.
editor = os.environ.get('EDITOR', None)
# On Windows systems, this script tries to determine the default text editor.

# Warning: DO NOT use an editor which doesn't support Unicode to edit pages!
# You will BREAK non-ASCII symbols!
editor_encoding = 'utf-8'

# The temporary file name extension can be set in order to use syntax
# highlighting in your text editor.
editor_filename_extension = 'wiki'

# ############# LOGFILE SETTINGS ##############

# Defines for which scripts a logfile should be enabled. Logfiles will be
# saved in the 'logs' subdirectory.
# Example:
#     log = ['interwiki', 'weblinkchecker', 'table2wiki']
# It is also possible to enable logging for all scripts, using this line:
#     log = ['*']
# To disable all logging, use this:
#     log = []
# Per default, logging of interwiki.py is enabled because its logfiles can
# be used to generate so-called warnfiles.
# This setting can be overridden by the -log or -nolog command-line arguments.
log = ['interwiki']
# filename defaults to modulename-bot.log
logfilename = None
# maximal size of a logfile in kilobytes. If the size reached that limit the
# logfile will be renamed (if logfilecount is not 0) and the old file is filled
# again. logfilesize must be an integer value
logfilesize = 1024
# Number of rotating logfiles are created. The older files get the higher
# number. If logfilecount is 0, no logfile will be archived but the current
# logfile will be overwritten if the file size reached the logfilesize above.
# If logfilecount is -1 there are no rotating logfiles but the files where
# renamed if the logfile is full. The newest file gets the highest number until
# some logfiles where deleted.
logfilecount = 5
# set to 1 (or higher) to generate "informative" messages to terminal
verbose_output = 0
# set to True to fetch the pywiki version online
log_pywiki_repo_version = False
# if True, include a lot of debugging info in logfile
# (overrides log setting above)
debug_log = []

# ############# INTERWIKI SETTINGS ##############

# Should interwiki.py report warnings for missing links between foreign
# languages?
interwiki_backlink = True

# Should interwiki.py display every new link it discovers?
interwiki_shownew = True

# Should interwiki.py output a graph PNG file on conflicts?
# You need pydot for this:
# https://pypi.python.org/pypi/pydot/1.0.2
# https://code.google.com/p/pydot/
interwiki_graph = False

# Specifies that the robot should process that amount of subjects at a time,
# only starting to load new pages in the original language when the total
# falls below that number. Default is to process (at least) 100 subjects at
# once.
interwiki_min_subjects = 100

# If interwiki graphs are enabled, which format(s) should be used?
# Supported formats include png, jpg, ps, and svg. See:
# http://www.graphviz.org/doc/info/output.html
# If you want to also dump the dot files, you can use this in your
# user-config.py:
# interwiki_graph_formats = ['dot', 'png']
# If you need a PNG image with an HTML image map, use this:
# interwiki_graph_formats = ['png', 'cmap']
# If you only need SVG images, use:
# interwiki_graph_formats = ['svg']
interwiki_graph_formats = ['png']

# You can post the contents of your autonomous_problems.dat to the wiki,
# e.g. to https://de.wikipedia.org/wiki/Wikipedia:Interwiki-Konflikte .
# This allows others to assist you in resolving interwiki problems.
# To help these people, you can upload the interwiki graphs to your
# webspace somewhere. Set the base URL here, e.g.:
# 'https://www.example.org/~yourname/interwiki-graphs/'
interwiki_graph_url = None

# Save file with local articles without interwikis.
without_interwiki = False

# Experimental feature:
# Store the page contents on disk (/cache/ directory) instead of loading
# them in RAM.
interwiki_contents_on_disk = False

# ############# SOLVE_DISAMBIGUATION SETTINGS ############
#
# Set disambiguation_comment[FAMILY][LANG] to a non-empty string to override
# the default edit comment for the solve_disambiguation bot.
# Use %s to represent the name of the disambiguation page being treated.
# Example:
#
# disambiguation_comment['wikipedia']['en'] = \
#    "Robot-assisted disambiguation ([[WP:DPL|you can help!]]): %s"

sort_ignore_case = False

# ############# IMAGE RELATED SETTINGS ##############
# If you set this to True, images will be uploaded to Wikimedia
# Commons by default.
upload_to_commons = False

# ############# SETTINGS TO AVOID SERVER OVERLOAD ##############

# Slow down the robot such that it never requests a second page within
# 'minthrottle' seconds. This can be lengthened if the server is slow,
# but never more than 'maxthrottle' seconds. However - if you are running
# more than one bot in parallel the times are lengthened.
# By default, the get_throttle is turned off, and 'maxlag' is used to
# control the rate of server access.  Set minthrottle to non-zero to use a
# throttle on read access.
minthrottle = 0
maxthrottle = 60

# Slow down the robot such that it never makes a second page edit within
# 'put_throttle' seconds.
put_throttle = 10

# Sometimes you want to know when a delay is inserted. If a delay is larger
# than 'noisysleep' seconds, it is logged on the screen.
noisysleep = 3.0

# Defer bot edits during periods of database server lag.  For details, see
# https://www.mediawiki.org/wiki/Maxlag_parameter
# You can set this variable to a number of seconds, or to None (or 0) to
# disable this behavior. Higher values are more aggressive in seeking
# access to the wiki.
# Non-Wikimedia wikis may or may not support this feature; for families
# that do not use it, it is recommended to set minthrottle (above) to
# at least 1 second.
maxlag = 5

# Maximum of pages which can be retrieved by special pages. Increase this if
# you heavily use redirect.py with action "double", and especially if you're
# running solve_disambiguation.py with the -primary argument.
special_page_limit = 500

# Maximum number of times to retry an API request before quitting.
max_retries = 25
# Minimum time to wait before resubmitting a failed API request.
retry_wait = 5

# ############# TABLE CONVERSION BOT SETTINGS ##############

# will split long paragraphs for better reading the source.
# only table2wiki.py use it by now
splitLongParagraphs = False
# sometimes HTML-tables are indented for better reading.
# That can do very ugly results.
deIndentTables = True
# table2wiki.py works quite stable, so you might switch to True
table2wikiAskOnlyWarnings = True
table2wikiSkipWarnings = False

# ############# WEBLINK CHECKER SETTINGS ##############

# How many external links should weblinkchecker.py check at the same time?
# If you have a fast connection, you might want to increase this number so
# that slow servers won't slow you down.
max_external_links = 50

report_dead_links_on_talk = False

# ############# DATABASE SETTINGS ##############
# Setting to connect the database or replica of the database of the wiki.
# db_name_format can be used to manipulate the dbName of site.
# Example for a pywikibot running on wmflabs:
# db_hostname = 'enwiki.labsdb'
# db_name_format = '{0}_p'
# db_connect_file = user_home_path('replica.my.cnf')
db_hostname = 'localhost'
db_username = ''
db_password = ''
db_name_format = '{0}'
db_connect_file = user_home_path('.my.cnf')

# ############# SEARCH ENGINE SETTINGS ##############

# Yahoo! Search Web Services are not operational.
# See https://phabricator.wikimedia.org/T106085
yahoo_appid = ''

# To use Windows Live Search web service you must get an AppID from
# http://www.bing.com/dev/en-us/dev-center
msn_appid = ''

# ############# FLICKR RIPPER SETTINGS ##############

# Using the Flickr api
flickr = {
    'api_key': u'',  # Provide your key!
    'api_secret': u'',  # Api secret of your key (optional)
    'review': False,  # Do we use automatically make our uploads reviewed?
    'reviewer': u'',  # If so, under what reviewer name?
}

# ############# COPYRIGHT SETTINGS ##############

# Enable/disable search engine in copyright.py script
copyright_google = True
copyright_yahoo = True
copyright_msn = False

# Perform a deep check, loading URLs to search if 'Wikipedia' is present.
# This may be useful to increase the number of correct results. If you haven't
# a fast connection, you might want to keep them disabled.
copyright_check_in_source_google = False
copyright_check_in_source_yahoo = False
copyright_check_in_source_msn = False

# Web pages may contain a Wikipedia text without the word 'Wikipedia' but with
# the typical '[edit]' tag as a result of a copy & paste procedure. You want
# no report for this kind of URLs, even if they are copyright violations.
# However, when enabled, these URLs are logged in a file.
copyright_check_in_source_section_names = False

# Limit number of queries for page.
copyright_max_query_for_page = 25

# Skip a specified number of queries
copyright_skip_query = 0

# Number of attempts on connection error.
copyright_connection_tries = 10

# Behavior if an exceeded error occur.
#
# Possibilities:
#
#    0 = None
#    1 = Disable search engine
#    2 = Sleep (default)
#    3 = Stop
copyright_exceeded_in_queries = 2
copyright_exceeded_in_queries_sleep_hours = 6

# Append last modified date of URL to script result
copyright_show_date = True

# Append length of URL to script result
copyright_show_length = True

# By default the script tries to identify and skip text that contains a large
# comma separated list or only numbers. But sometimes that might be the
# only part unmodified of a slightly edited and not otherwise reported
# copyright violation. You can disable this feature to try to increase the
# number of results.
copyright_economize_query = True

# ############# HTTP SETTINGS ##############
# Use a persistent http connection. An http connection has to be established
# only once per site object, making stuff a whole lot faster. Do NOT EVER
# use this if you share Site objects across threads without proper locking.
#
# DISABLED FUNCTION. Setting this variable will not have any effect.
persistent_http = False

# Default socket timeout. Set to None to disable timeouts.
socket_timeout = 120  # set a pretty long timeout just in case...


# ############# COSMETIC CHANGES SETTINGS ##############
# The bot can make some additional changes to each page it edits, e.g. fix
# whitespace or positioning of interwiki and category links.

# This is an experimental feature; handle with care and consider re-checking
# each bot edit if enabling this!
cosmetic_changes = False

# If cosmetic changes are switched on, and you also have several accounts at
# projects where you're not familiar with the local conventions, you probably
# only want the bot to do cosmetic changes on your "home" wiki which you
# specified in config.mylang and config.family.
# If you want the bot to also do cosmetic changes when editing a page on a
# foreign wiki, set cosmetic_changes_mylang_only to False, but be careful!
cosmetic_changes_mylang_only = True

# The dictionary cosmetic_changes_enable should contain a tuple of languages
# for each site where you wish to enable in addition to your own langlanguage
# (if cosmetic_changes_mylang_only is set)
# Please set your dictionary by adding such lines to your user-config.py:
# cosmetic_changes_enable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_enable = {}

# The dictionary cosmetic_changes_disable should contain a tuple of languages
# for each site where you wish to disable cosmetic changes. You may use it with
# cosmetic_changes_mylang_only is False, but you can also disable your own
# language. This also overrides the settings in the cosmetic_changes_enable
# dictionary. Please set your dict by adding such lines to your user-config.py:
# cosmetic_changes_disable['wikipedia'] = ('de', 'en', 'fr')
cosmetic_changes_disable = {}

# cosmetic_changes_deny_script is a list of scripts for which cosmetic changes
# are disabled. You may add additional scripts by appending script names in
# your user_config.py ("+=" operator is strictly recommended):
# cosmetic_changes_deny_script += ['your_script_name_1', 'your_script_name_2']
# Appending the script name also works:
# cosmetic_changes_deny_script.append('your_script_name')
cosmetic_changes_deny_script = ['category_redirect', 'cosmetic_changes',
                                'newitem', 'touch']

# ############# REPLICATION BOT ################
# You can add replicate_replace to your user_config.py, which has the following
# format:
#
# replicate_replace = {
#            'wikipedia:li': {'Hoofdpagina': 'Veurblaad'}
# }
#
# to replace all occurrences of 'Hoofdpagina' with 'Veurblaad' when writing to
# liwiki. Note that this does not take the origin wiki into account.
replicate_replace = {}

# ############# FURTHER SETTINGS ##############

# Proxy configuration

# For proxy support, install socksipy or httplib2 0.7+
# then add these three lines to your user-config.py:
# from httplib2 import ProxyInfo, socks
# proxy = ProxyInfo(socks.PROXY_TYPE_HTTP, 'localhost', 8000)
# del ProxyInfo, socks
proxy = None

# Simulate settings

# Defines what additional actions the bots are NOT allowed to do (e.g. 'edit')
# on the wiki server. Allows simulation runs of bots to be carried out without
# changing any page on the server side. Use this setting to add more actions
# in user-config.py for wikis with extra write actions.
actions_to_block = []

# Set simulate to True or use -simulate option to block all actions given above.
simulate = False

# How many pages should be put to a queue in asynchronous mode.
# If maxsize is <= 0, the queue size is infinite.
# Increasing this value will increase memory space but could speed up
# processing. As higher this value this effect will decrease.
max_queue_size = 64

# Define the line separator. Pages retrieved via API have "\n" whereas
# pages fetched from screen (mostly) have "\r\n". Interwiki and category
# separator settings in family files should use multiplied of this.
# LS is a shortcut alias.
line_separator = LS = u'\n'

# Settings to enable mwparserfromhell
# <https://mwparserfromhell.readthedocs.org/en/latest/>
# Currently used in textlib.extract_templates_and_params
# This is more accurate than our current regex, but only works
# if the user has already installed the library.
use_mwparserfromhell = True

# Pickle protocol version to use for storing dumps.
# This config variable is not used for loading dumps.
# Version 2 is common to both Python 2 and 3, and should
# be used when dumps are accessed by both versions.
# Version 4 is only available for Python 3.4
pickle_protocol = 2

# End of configuration section
# ============================


def makepath(path):
    """Return a normalized absolute version of the path argument.

     - if the given path already exists in the filesystem
       the filesystem is not modified.
     - otherwise makepath creates directories along the given path
       using the dirname() of the path. You may append
       a '/' to the path if you want it to be a directory path.

    from holger@trillke.net 2002/03/18

    """
    dpath = os.path.normpath(os.path.dirname(path))
    if not os.path.exists(dpath):
        os.makedirs(dpath)
    return os.path.normpath(os.path.abspath(path))


def datafilepath(*filename):
    """Return an absolute path to a data file in a standard location.

    Argument(s) are zero or more directory names, optionally followed by a
    data file name. The return path is offset to config.base_dir. Any
    directories in the path that do not already exist are created.

    """
    return makepath(os.path.join(base_dir, *filename))


def shortpath(path):
    """Return a file path relative to config.base_dir."""
    if path.startswith(base_dir):
        return path[len(base_dir) + len(os.path.sep):]
    return path


def _win32_extension_command(extension):
    """Get the command from the Win32 registry for an extension."""
    fileexts_key = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts'
    key_name = fileexts_key + r'\.' + extension + r'\OpenWithProgids'
    _winreg = winreg  # exists for git blame only; do not use
    try:
        key1 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name)
        _progID = winreg.EnumValue(key1, 0)[0]
        _key2 = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT,
                                '%s\shell\open\command' % _progID)
        _cmd = _winreg.QueryValueEx(_key2, None)[0]
        # See T102465 for issues relating to using this value.
        cmd = _cmd
        if cmd.find('%1'):
            cmd = cmd[:cmd.find('%1')]
            # Remove any trailing characher, which should be a quote or space
            # and then remove all whitespace.
            return cmd[:-1].strip()
    except WindowsError as e:
        # Catch any key lookup errors
        print('WARNING: Unable to find editor for files *.' + extension)
        print(e)


def _detect_win32_editor():
    """Detect the best Win32 editor."""
    # Notepad is even worse than our Tkinter editor.
    unusable_exes = ['notepad.exe',
                     'py.exe',
                     'pyw.exe',
                     'python.exe',
                     'pythonw.exe']

    for ext in ['py', 'txt']:
        editor = _win32_extension_command(ext)
        if editor:
            for unusable in unusable_exes:
                if unusable in editor.lower():
                    break
            else:
                return editor


# System-level and User-level changes.
# Store current variables and their types.
_glv = dict((_key, _val) for _key, _val in globals().items()
             if _key[0] != '_' and _key not in _imports)
_gl = list(_glv.keys())
_tp = {}
for _key in _gl:
    _tp[_key] = type(globals()[_key])

# Create an environment for user-config.py which is
# a shallow copy of the core config settings, so that
# we can detect modified config items easily.
_uc = {}
for _key, _val in _glv.items():
    if isinstance(_val, dict):
        if isinstance(_val, collections.defaultdict):
            _uc[_key] = collections.defaultdict(dict)
        else:
            _uc[_key] = {}
        if len(_val) > 0:
            _uc[_key].update(_val)
    else:
        _uc[_key] = _val

# Get the user files
_thislevel = 0
if __no_user_config:
    if __no_user_config != '2':
        print("WARNING: Skipping loading of user-config.py.")
    _fns = []
else:
    _fns = [os.path.join(_base_dir, "user-config.py")]
for _filename in _fns:
    _thislevel += 1
    if os.path.exists(_filename):
        _filestatus = os.stat(_filename)
        _filemode = _filestatus[0]
        _fileuid = _filestatus[4]
        if sys.platform == 'win32' or _fileuid in [os.getuid(), 0]:
            if sys.platform == 'win32' or _filemode & 0o02 == 0:
                with open(_filename, 'rb') as f:
                    exec(compile(f.read(), _filename, 'exec'), _uc)
            else:
                print("WARNING: Skipped '%(fn)s': writeable by others."
                      % {'fn': _filename})
        else:
            print("WARNING: Skipped '%(fn)s': owned by someone else."
                  % {'fn': _filename})

# Test for obsoleted and/or unknown variables.
for _key, _val in list(_uc.items()):
    if _key.startswith('_'):
        pass
    elif _key in _imports:
        pass
    elif _key in _gl:
        nt = type(_val)
        ot = _tp[_key]
        ov = _glv[_key]

        if nt == ot or _val is None or ov is None:  # nopep8
            pass
        elif nt is int and (ot is float or ot is bool):
            pass
        elif ot is int and (nt is float or nt is bool):
            pass
        else:
            print("WARNING: Type of '%(_key)s' changed" % locals())
            print("         %(was)s: %(old)s" % {'was': "Was", 'old': ot})
            print("         %(now)s: %(new)s" % {'now': "Now", 'new': nt})
        del nt, ot, ov
    else:
        print("WARNING: "
              "Configuration variable %(_key)r is defined but unknown.\n"
              "Misspelled?" % locals())

# Copy the user config settings into globals
_modified = [_key for _key in _gl
             if _uc[_key] != globals()[_key] or
             _key in ('usernames', 'sysopnames', 'disambiguation_comment')]

for _key in _modified:
    globals()[_key] = _uc[_key]

    if _key in _deprecated_variables:
        warn("'%s' is no longer a supported configuration variable.\n"
             "Please inform the maintainers if you depend on it." % _key,
             _ConfigurationDeprecationWarning)

# Fix up default console_encoding
if console_encoding is None:
    if sys.platform == 'win32':
        console_encoding = 'cp850'
    else:
        console_encoding = 'iso-8859-1'


if sys.platform == 'win32' and editor is None:
    editor = _detect_win32_editor()

if sys.platform == 'win32' and editor:
    # single character string literals from
    # https://docs.python.org/2/reference/lexical_analysis.html#string-literals
    # encode('unicode-escape') also changes Unicode characters
    if set(editor) & set('\a\b\f\n\r\t\v'):
        print('WARNING: The editor path contains probably invalid escaped '
              'characters. Make sure to use a raw-string (r"..." or r\'...\'), '
              'forward slashs as a path delimiter or to escape the normal '
              'path delimiter.')


# Fix up default site
if family == 'wikipedia' and mylang == 'language' and __no_user_config != '2':
    print("WARNING: family and mylang are not set.\n"
          "Defaulting to family='test' and mylang='test'.")
    family = mylang = 'test'

# SECURITY WARNINGS
if (not ignore_file_security_warnings and
        private_files_permission & (stat.S_IRWXG | stat.S_IRWXO) != 0):
    print("CRITICAL SECURITY WARNING: 'private_files_permission' is set"
          " to allow access from the group/others which"
          " could give them access to the sensitive files."
          " To avoid giving others access to sensitive files, pywikibot"
          " won't run with this setting. Choose a more restrictive"
          " permission or set 'ignore_file_security_warnings' to true.")
    sys.exit(1)

#
# When called as main program, list all configuration variables
#
if __name__ == "__main__":
    import types
    _all = 1
    for _arg in sys.argv[1:]:
        if _arg == "modified":
            _all = 0
        else:
            print("Unknown arg %(_arg)s ignored" % locals())
    _k = list(globals().keys())
    _k.sort()
    for _name in _k:
        if _name[0] != '_':
            if not type(globals()[_name]) in [types.FunctionType,
                                              types.ModuleType]:
                if _all or _name in _modified:
                    _value = globals()[_name]
                    if _name in _private_values and _value:
                        if isinstance(_value, dict):
                            _value = '{ ...xxxxxxxx... }'
                        elif hasattr(_value, '__dict__'):
                            _value = '%s( ...xxxxxxxx... )' % \
                                     _value.__class__.__name__
                        else:
                            _value = repr('xxxxxxxx')
                    else:
                        _value = repr(_value)
                    print("%s=%s" % (_name, _value))

# cleanup all locally-defined variables
for __var in list(globals().keys()):
    if __var.startswith("_") and not __var.startswith("__"):
        del sys.modules[__name__].__dict__[__var]

del __var
