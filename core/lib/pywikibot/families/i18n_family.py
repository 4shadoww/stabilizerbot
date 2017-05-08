# -*- coding: utf-8  -*-
"""Family module for Translate Wiki."""
from __future__ import unicode_literals

__version__ = '$Id: dc75d8df0b2df25d5d19a7bea49e2877b0cffdd4 $'

from pywikibot import family


# The Wikimedia i18n family
class Family(family.Family):

    """Family class for Translate Wiki."""

    name = 'i18n'
    langs = {'i18n': 'translatewiki.net'}

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"
