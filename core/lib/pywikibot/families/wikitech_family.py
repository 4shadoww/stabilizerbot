# -*- coding: utf-8  -*-
"""Family module for Wikitech."""
from __future__ import unicode_literals

__version__ = '$Id: 5cba33c05874a5b4074c5dd7aa04a7e16a8279c2 $'

from pywikibot import family


# The Wikitech family
class Family(family.Family):

    """Family class for Wikitech."""

    name = 'wikitech'
    langs = {'en': 'wikitech.wikimedia.org'}

    def protocol(self, code):
        """Return the protocol for this family."""
        return 'https'
