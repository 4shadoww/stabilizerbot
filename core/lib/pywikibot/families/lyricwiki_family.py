# -*- coding: utf-8  -*-
"""Family module for LyricWiki."""
from __future__ import unicode_literals

__version__ = '$Id: 0839ff94f1ffc2dac4ee604d132026225c7f0549 $'

from pywikibot import family


# The LyricWiki family

# user_config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.Family):

    """Family class for LyricWiki."""

    name = 'lyricwiki'
    langs = {
        'en': 'lyrics.wikia.com',
    }

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''
