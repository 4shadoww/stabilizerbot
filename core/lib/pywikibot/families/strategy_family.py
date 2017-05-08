# -*- coding: utf-8  -*-
"""Family module for Wikimedia Strategy Wiki."""
from __future__ import unicode_literals

__version__ = '$Id: 3d3570cde504f7fa5a46107ce6debdfb8338afc4 $'

from pywikibot import family


# The Wikimedia Strategy family
class Family(family.WikimediaFamily):

    """Family class for Wikimedia Strategy Wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'strategy'
        self.langs = {
            'strategy': 'strategy.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'

    def dbName(self, code):
        """Return the database name for this family."""
        return 'strategywiki_p'
