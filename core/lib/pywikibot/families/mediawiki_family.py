# -*- coding: utf-8  -*-
"""Family module for MediaWiki wiki."""
from __future__ import unicode_literals

__version__ = '$Id: 8c9856dd7c0af8d400d0d95b00bf406002729008 $'

from pywikibot import family


# The MediaWiki family
# user-config.py: usernames['mediawiki']['mediawiki'] = 'User name'
class Family(family.WikimediaFamily):

    """Family module for MediaWiki wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'mediawiki'

        self.langs = {
            'mediawiki': 'www.mediawiki.org',
        }
