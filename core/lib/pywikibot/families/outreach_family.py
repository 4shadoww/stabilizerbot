# -*- coding: utf-8  -*-
"""Family module for Wikimedia outreach wiki."""
from __future__ import unicode_literals

__version__ = '$Id: 8ad23b6dfa568979f3dc447ae38245027fd2cd68 $'

from pywikibot import family


# Outreach wiki custom family
class Family(family.WikimediaFamily):

    """Family class for Wikimedia outreach wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = u'outreach'
        self.langs = {
            'outreach': 'outreach.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
