# -*- coding: utf-8  -*-
"""Family module for Wikidata."""
from __future__ import unicode_literals

__version__ = '$Id: 13f5546722cc88c1f3604d304636dc97b5a0376b $'

from pywikibot import family

# The Wikidata family


class Family(family.WikimediaFamily):

    """Family class for Wikidata."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikidata'
        self.langs = {
            'wikidata': 'www.wikidata.org',
            'test': 'test.wikidata.org',
        }

        self.interwiki_forward = 'wikipedia'

        # Subpages for documentation.
        self.doc_subpages = {
            '_default': ((u'/doc', ), ['wikidata']),
        }

    def shared_data_repository(self, code, transcluded=False):
        """
        Indicate Wikidata is both a repository and its own client.

        Until 20 August 2014, Wikidata was only a data repository,
        and this method only returned a tuple with data if
        transcluded was False.

        On that date, the software was enhanced so that Wikidata
        could store sitelinks to itself.
        """
        return (code, self.name)

    def calendarmodel(self, code):
        """Default calendar model for WbTime datatype."""
        return 'http://www.wikidata.org/entity/Q1985727'

    def globes(self, code):
        """Supported globes for Coordinate datatype."""
        return {
            'ariel': 'http://www.wikidata.org/entity/Q3343',
            'callisto': 'http://www.wikidata.org/entity/Q3134',
            'ceres': 'http://www.wikidata.org/entity/Q596',
            'deimos': 'http://www.wikidata.org/entity/Q7548',
            'dione': 'http://www.wikidata.org/entity/Q15040',
            'earth': 'http://www.wikidata.org/entity/Q2',
            'enceladus': 'http://www.wikidata.org/entity/Q3303',
            'eros': 'http://www.wikidata.org/entity/Q16711',
            'europa': 'http://www.wikidata.org/entity/Q3143',
            'ganymede': 'http://www.wikidata.org/entity/Q3169',
            'gaspra': 'http://www.wikidata.org/entity/Q158244',
            'hyperion': 'http://www.wikidata.org/entity/Q15037',
            'iapetus': 'http://www.wikidata.org/entity/Q17958',
            'io': 'http://www.wikidata.org/entity/Q3123',
            'jupiter': 'http://www.wikidata.org/entity/Q319',
            'lutetia': 'http://www.wikidata.org/entity/Q107556',
            'mars': 'http://www.wikidata.org/entity/Q111',
            'mercury': 'http://www.wikidata.org/entity/Q308',
            'mimas': 'http://www.wikidata.org/entity/Q15034',
            'miranda': 'http://www.wikidata.org/entity/Q3352',
            'moon': 'http://www.wikidata.org/entity/Q405',
            'oberon': 'http://www.wikidata.org/entity/Q3332',
            'phobos': 'http://www.wikidata.org/entity/Q7547',
            'phoebe': 'http://www.wikidata.org/entity/Q17975',
            'pluto': 'http://www.wikidata.org/entity/Q339',
            'rhea': 'http://www.wikidata.org/entity/Q15050',
            'tethys': 'http://www.wikidata.org/entity/Q15047',
            'titan': 'http://www.wikidata.org/entity/Q2565',
            'titania': 'http://www.wikidata.org/entity/Q3322',
            'triton': 'http://www.wikidata.org/entity/Q3359',
            'umbriel': 'http://www.wikidata.org/entity/Q3338',
            'venus': 'http://www.wikidata.org/entity/Q313',
            'vesta': 'http://www.wikidata.org/entity/Q3030',
        }
