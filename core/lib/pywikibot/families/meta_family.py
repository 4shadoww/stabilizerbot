# -*- coding: utf-8  -*-
"""Family module for Meta Wiki."""
from __future__ import unicode_literals

__version__ = '$Id: eeb4b27d3dbf58adf86e32c33bc6e17d22088141 $'

from pywikibot import family


# The meta wikimedia family
class Family(family.WikimediaFamily):

    """Family class for Meta Wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'meta'
        self.langs = {
            'meta': 'meta.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
        self.cross_allowed = ['meta', ]
