# -*- coding: utf-8  -*-
"""Family module for Incubator Wiki."""
from __future__ import unicode_literals

__version__ = '$Id: 5f0ad41a79b798f25caeb2af9e2e30cb9f0e40d9 $'

from pywikibot import family


# The Wikimedia Incubator family
class Family(family.WikimediaFamily):

    """Family class for Incubator Wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }
