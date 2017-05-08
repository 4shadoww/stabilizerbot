# -*- coding: utf-8  -*-
"""
Functions for manipulating wiki-text.

Unless otherwise noted, all functions take a unicode string as the argument
and return a unicode string.

"""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id: 456940e96bf45d41ef518a74c4732ad72ce06c3e $'
#

import datetime
import re
import sys

if sys.version_info[0] > 2:
    from html.parser import HTMLParser
    basestring = (str,)
    unicode = str
else:
    from HTMLParser import HTMLParser

import pywikibot

from pywikibot import config2 as config
from pywikibot.family import Family
from pywikibot.tools import (
    OrderedDict,
    issue_deprecation_warning
)

# cache for replaceExcept to avoid recompile or regexes each call
_regex_cache = {}

TEMP_REGEX = re.compile(
    r'{{(?:msg:)?(?P<name>[^{\|]+?)(?:\|(?P<params>[^{]+?(?:{[^{]+?}[^{]*?)?))?}}')

NON_LATIN_DIGITS = {
    'ckb': u'٠١٢٣٤٥٦٧٨٩',
    'fa': u'۰۱۲۳۴۵۶۷۸۹',
    'km': u'០១២៣៤៥៦៧៨៩',
    'kn': u'೦೧೨೩೪೫೬೭೮೯',
    'bn': u'০১২৩৪৫৬৭৮৯',
    'gu': u'૦૧૨૩૪૫૬૭૮૯',
    'or': u'୦୧୨୩୪୫୬୭୮୯',
}


def to_local_digits(phrase, lang):
    """
    Change Latin digits based on language to localized version.

    Be aware that this function only returns for several language
    And doesn't touch the input if other languages are asked.
    @param phrase: The phrase to convert to localized numerical
    @param lang: language code
    @return: The localized version
    @rtype: unicode
    """
    digits = NON_LATIN_DIGITS.get(lang)
    if not digits:
        return phrase
    phrase = u"%s" % phrase
    for i in range(10):
        phrase = phrase.replace(str(i), digits[i])
    return phrase


def unescape(s):
    """Replace escaped HTML-special characters by their originals."""
    if '&' not in s:
        return s
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&apos;", "'")
    s = s.replace("&quot;", '"')
    s = s.replace("&amp;", "&")  # Must be last
    return s


def _create_default_regexes():
    """Fill (and possibly overwrite) _regex_cache with default regexes."""
    _regex_cache.update({
        'comment':      re.compile(r'(?s)<!--.*?-->'),
        # section headers
        'header':       re.compile(r'\r?\n=+.+=+ *\r?\n'),
        # preformatted text
        'pre':          re.compile(r'(?ism)<pre>.*?</pre>'),
        'source':       re.compile(r'(?is)<source .*?</source>'),
        # inline references
        'ref':          re.compile(r'(?ism)<ref[ >].*?</ref>'),
        # lines that start with a space are shown in a monospace font and
        # have whitespace preserved.
        'startspace':   re.compile(r'(?m)^ (.*?)$'),
        # tables often have whitespace that is used to improve wiki
        # source code readability.
        # TODO: handle nested tables.
        'table':        re.compile(r'(?ims)^{\|.*?^\|}|<table>.*?</table>'),
        'hyperlink':    compileLinkR(),
        'gallery':      re.compile(r'(?is)<gallery.*?>.*?</gallery>'),
        # this matches internal wikilinks, but also interwiki, categories, and
        # images.
        'link':         re.compile(r'\[\[[^\]\|]*(\|[^\]]*)?\]\]'),
        # also finds links to foreign sites with preleading ":"
        'interwiki':    (r'(?i)\[\[:?(%s)\s?:[^\]]*\]\][\s]*',
                         lambda site: '|'.join(
                             site.validLanguageLinks() +
                             list(site.family.obsolete.keys()))),
        # Wikibase property inclusions
        'property':     re.compile(r'(?i)\{\{\s*#property:\s*p\d+\s*\}\}'),
        # Module invocations (currently only Lua)
        'invoke':       re.compile(r'(?i)\{\{\s*#invoke:.*?}\}'),
        # categories
        'category':     ('\[\[ *(?:%s)\s*:.*?\]\]',
                         lambda site: '|'.join(site.namespaces[14])),
        # files
        'file':         ('\[\[ *(?:%s)\s*:.*?\]\]',
                         lambda site: '|'.join(site.namespaces[6])),
    })


def _get_regexes(keys, site):
    """Fetch compiled regexes."""
    if site is None:
        site = pywikibot.Site()

    if not _regex_cache:
        _create_default_regexes()

    result = []
    # 'dontTouchRegexes' exist to reduce git blame only.
    dontTouchRegexes = result

    for exc in keys:
        if isinstance(exc, basestring):
            # assume the string is a reference to a standard regex above,
            # which may not yet have a site specific re compiled.
            if exc in _regex_cache:
                if type(_regex_cache[exc]) is tuple:
                    if (exc, site) not in _regex_cache:
                        re_text, re_var = _regex_cache[exc]
                        _regex_cache[(exc, site)] = re.compile(
                            re_text % re_var(site))

                    result.append(_regex_cache[(exc, site)])
                else:
                    result.append(_regex_cache[exc])
            elif exc == 'template':
                # template is not supported by this method.
                pass
            else:
                # nowiki, noinclude, includeonly, timeline, math ond other
                # extensions
                if exc not in _regex_cache:
                    _regex_cache[exc] = re.compile(r'(?is)<%s>.*?</%s>'
                                                    % (exc, exc))
                result.append(_regex_cache[exc])
            # handle alias
            if exc == 'source':
                dontTouchRegexes.append(re.compile(
                    r'(?is)<syntaxhighlight .*?</syntaxhighlight>'))
        else:
            # assume it's a regular expression
            dontTouchRegexes.append(exc)

    return result


def replaceExcept(text, old, new, exceptions, caseInsensitive=False,
                  allowoverlap=False, marker='', site=None):
    """
    Return text with 'old' replaced by 'new', ignoring specified types of text.

    Skips occurrences of 'old' within exceptions; e.g., within nowiki tags or
    HTML comments. If caseInsensitive is true, then use case insensitive
    regex matching. If allowoverlap is true, overlapping occurrences are all
    replaced (watch out when using this, it might lead to infinite loops!).

    @type text: unicode
    @param old: a compiled or uncompiled regular expression
    @param new: a unicode string (which can contain regular
        expression references), or a function which takes
        a match object as parameter. See parameter repl of
        re.sub().
    @param exceptions: a list of strings which signal what to leave out,
        e.g. ['math', 'table', 'template']
    @type caseInsensitive: bool
    @param marker: a string that will be added to the last replacement;
        if nothing is changed, it is added at the end

    """
    # if we got a string, compile it as a regular expression
    if isinstance(old, basestring):
        if caseInsensitive:
            old = re.compile(old, re.IGNORECASE | re.UNICODE)
        else:
            old = re.compile(old)

    # early termination if not relevant
    if not old.search(text):
        return text + marker

    dontTouchRegexes = _get_regexes(exceptions, site)

    except_templates = 'template' in exceptions

    # mark templates
    # don't care about mw variables and parser functions
    if except_templates:
        marker1 = findmarker(text)
        marker2 = findmarker(text, u'##', u'#')
        Rvalue = re.compile('{{{.+?}}}')
        Rmarker1 = re.compile(r'%(mark)s(\d+)%(mark)s' % {'mark': marker1})
        Rmarker2 = re.compile(r'%(mark)s(\d+)%(mark)s' % {'mark': marker2})
        # hide the flat template marker
        dontTouchRegexes.append(Rmarker1)
        origin = text
        values = {}
        count = 0
        for m in Rvalue.finditer(text):
            count += 1
            # If we have digits between brackets, restoring from dict may fail.
            # So we need to change the index. We have to search in the origin.
            while u'}}}%d{{{' % count in origin:
                count += 1
            item = m.group()
            text = text.replace(item, '%s%d%s' % (marker2, count, marker2))
            values[count] = item
        inside = {}
        seen = set()
        count = 0
        while TEMP_REGEX.search(text) is not None:
            for m in TEMP_REGEX.finditer(text):
                item = m.group()
                if item in seen:
                    continue  # speed up
                seen.add(item)
                count += 1
                while u'}}%d{{' % count in origin:
                    count += 1
                text = text.replace(item, '%s%d%s' % (marker1, count, marker1))

                # Make sure stored templates don't contain markers
                for m2 in Rmarker1.finditer(item):
                    item = item.replace(m2.group(), inside[int(m2.group(1))])
                for m2 in Rmarker2.finditer(item):
                    item = item.replace(m2.group(), values[int(m2.group(1))])
                inside[count] = item
    index = 0
    markerpos = len(text)
    while True:
        if index > len(text):
            break
        match = old.search(text, index)
        if not match:
            # nothing left to replace
            break

        # check which exception will occur next.
        nextExceptionMatch = None
        for dontTouchR in dontTouchRegexes:
            excMatch = dontTouchR.search(text, index)
            if excMatch and (
                    nextExceptionMatch is None or
                    excMatch.start() < nextExceptionMatch.start()):
                nextExceptionMatch = excMatch

        if nextExceptionMatch is not None \
                and nextExceptionMatch.start() <= match.start():
            # an HTML comment or text in nowiki tags stands before the next
            # valid match. Skip.
            index = nextExceptionMatch.end()
        else:
            # We found a valid match. Replace it.
            if callable(new):
                # the parameter new can be a function which takes the match
                # as a parameter.
                replacement = new(match)
            else:
                # it is not a function, but a string.

                # it is a little hack to make \n work. It would be better
                # to fix it previously, but better than nothing.
                new = new.replace('\\n', '\n')

                # We cannot just insert the new string, as it may contain regex
                # group references such as \2 or \g<name>.
                # On the other hand, this approach does not work because it
                # can't handle lookahead or lookbehind (see bug #1731008):
                #
                #  replacement = old.sub(new, text[match.start():match.end()])
                #  text = text[:match.start()] + replacement + text[match.end():]

                # So we have to process the group references manually.
                replacement = ''

                group_regex = re.compile(r'\\(\d+)|\\g<(.+?)>')
                last = 0
                for group_match in group_regex.finditer(new):
                    group_id = group_match.group(1) or group_match.group(2)
                    try:
                        group_id = int(group_id)
                    except ValueError:
                        pass
                    try:
                        replacement += new[last:group_match.start()]
                        replacement += match.group(group_id) or ''
                    except IndexError:
                        pywikibot.output('\nInvalid group reference: %s' % group_id)
                        pywikibot.output('Groups found:\n%s' % match.groups())
                        raise IndexError
                    last = group_match.end()
                replacement += new[last:]

            text = text[:match.start()] + replacement + text[match.end():]

            # continue the search on the remaining text
            if allowoverlap:
                index = match.start() + 1
            else:
                index = match.start() + len(replacement)
            if not match.group():
                # When the regex allows to match nothing, shift by one character
                index += 1
            markerpos = match.start() + len(replacement)
    text = text[:markerpos] + marker + text[markerpos:]

    if except_templates:  # restore templates from dict
        for m2 in Rmarker1.finditer(text):
            text = text.replace(m2.group(), inside[int(m2.group(1))])
        for m2 in Rmarker2.finditer(text):
            text = text.replace(m2.group(), values[int(m2.group(1))])
    return text


def removeDisabledParts(text, tags=['*'], include=[]):
    """
    Return text without portions where wiki markup is disabled.

    Parts that can/will be removed are --
    * HTML comments
    * nowiki tags
    * pre tags
    * includeonly tags

    The exact set of parts which should be removed can be passed as the
    'tags' parameter, which defaults to all.
    Or, in alternative, default parts that shall not be removed can be
    specified in the 'include' param.

    """
    regexes = {
        'comments':        r'<!--.*?-->',
        'includeonly':     r'<includeonly>.*?</includeonly>',
        'nowiki':          r'<nowiki>.*?</nowiki>',
        'pre':             r'<pre>.*?</pre>',
        'source':          r'<source .*?</source>',
        'syntaxhighlight': r'<syntaxhighlight .*?</syntaxhighlight>',
    }
    if '*' in tags:
        tags = list(regexes.keys())
    # add alias
    tags = set(tags) - set(include)
    if 'source' in tags:
        tags.add('syntaxhighlight')
    toRemoveR = re.compile('|'.join([regexes[tag] for tag in tags]),
                           re.IGNORECASE | re.DOTALL)
    return toRemoveR.sub('', text)


def removeHTMLParts(text, keeptags=['tt', 'nowiki', 'small', 'sup']):
    """
    Return text without portions where HTML markup is disabled.

    Parts that can/will be removed are --
    * HTML and all wiki tags

    The exact set of parts which should NOT be removed can be passed as the
    'keeptags' parameter, which defaults to ['tt', 'nowiki', 'small', 'sup'].

    """
    # try to merge with 'removeDisabledParts()' above into one generic function
    # thanks to https://www.hellboundhackers.org/articles/read-article.php?article_id=841
    parser = _GetDataHTML()
    parser.keeptags = keeptags
    parser.feed(text)
    parser.close()
    return parser.textdata


# thanks to https://docs.python.org/2/library/htmlparser.html
class _GetDataHTML(HTMLParser):
    textdata = u''
    keeptags = []

    def handle_data(self, data):
        self.textdata += data

    def handle_starttag(self, tag, attrs):
        if tag in self.keeptags:
            self.textdata += u"<%s>" % tag

    def handle_endtag(self, tag):
        if tag in self.keeptags:
            self.textdata += u"</%s>" % tag


def isDisabled(text, index, tags=['*']):
    """
    Return True if text[index] is disabled, e.g. by a comment or by nowiki tags.

    For the tags parameter, see L{removeDisabledParts}.
    """
    # Find a marker that is not already in the text.
    marker = findmarker(text)
    text = text[:index] + marker + text[index:]
    text = removeDisabledParts(text, tags)
    return (marker not in text)


def findmarker(text, startwith=u'@@', append=None):
    """Find a string which is not part of text."""
    if not append:
        append = u'@'
    mymarker = startwith
    while mymarker in text:
        mymarker += append
    return mymarker


def expandmarker(text, marker='', separator=''):
    # set to remove any number of separator occurrences plus arbitrary
    # whitespace before, after, and between them,
    # by allowing to include them into marker.
    if separator:
        firstinmarker = text.find(marker)
        firstinseparator = firstinmarker
        lenseparator = len(separator)
        striploopcontinue = True
        while firstinseparator > 0 and striploopcontinue:
            striploopcontinue = False
            if (firstinseparator >= lenseparator) and \
               (separator == text[firstinseparator -
                                  lenseparator:firstinseparator]):
                firstinseparator -= lenseparator
                striploopcontinue = True
            elif text[firstinseparator - 1] < ' ':
                firstinseparator -= 1
                striploopcontinue = True
        marker = text[firstinseparator:firstinmarker] + marker
    return marker


# -----------------------------------------------
# Functions dealing with interwiki language links
# -----------------------------------------------
# Note - MediaWiki supports several kinds of interwiki links; two kinds are
#        inter-language links. We deal here with those kinds only.
#        A family has by definition only one kind of inter-language links:
#        1 - inter-language links inside the own family.
#            They go to a corresponding page in another language in the same
#            family, such as from 'en.wikipedia' to 'pt.wikipedia', or from
#            'es.wiktionary' to 'arz.wiktionary'.
#            Families with this kind have several language-specific sites.
#            They have their interwiki_forward attribute set to None
#        2 - language links forwarding to another family.
#            They go to a corresponding page in another family, such as from
#            'commons' to 'zh.wikipedia, or from 'incubator' to 'en.wikipedia'.
#            Families having those have one member only, and do not have
#            language-specific sites. The name of the target family of their
#            inter-language links is kept in their interwiki_forward attribute.
#        These functions only deal with links of these two kinds only.  They
#        do not find or change links of other kinds, nor any that are formatted
#        as in-line interwiki links (e.g., "[[:es:Articulo]]".

def getLanguageLinks(text, insite=None, pageLink="[[]]",
                     template_subpage=False):
    """
    Return a dict of inter-language links found in text.

    The returned dict uses the site as keys and Page objects as values. It does
    not contain its own site.

    Do not call this routine directly, use Page.interwiki() method
    instead.

    """
    if insite is None:
        insite = pywikibot.Site()
    fam = insite.family
    # when interwiki links forward to another family, retrieve pages & other
    # infos there
    if fam.interwiki_forward:
        fam = Family.load(fam.interwiki_forward)
    result = {}
    # Ignore interwiki links within nowiki tags, includeonly tags, pre tags,
    # and HTML comments
    tags = ['comments', 'nowiki', 'pre', 'source']
    if not template_subpage:
        tags += ['includeonly']
    text = removeDisabledParts(text, tags)

    # This regular expression will find every link that is possibly an
    # interwiki link.
    # NOTE: language codes are case-insensitive and only consist of basic latin
    # letters and hyphens.
    # TODO: currently, we do not have any, but BCP 47 allows digits, and
    #       underscores.
    # TODO: There is no semantic difference between hyphens and
    #       underscores -> fold them.
    interwikiR = re.compile(r'\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]')
    for lang, pagetitle in interwikiR.findall(text):
        lang = lang.lower()
        # Check if it really is in fact an interwiki link to a known
        # language, or if it's e.g. a category tag or an internal link
        if lang in fam.obsolete:
            lang = fam.obsolete[lang]
        if lang in list(fam.langs.keys()):
            if '|' in pagetitle:
                # ignore text after the pipe
                pagetitle = pagetitle[:pagetitle.index('|')]
            # we want the actual page objects rather than the titles
            site = pywikibot.Site(code=lang, fam=fam)
            # skip language links to its own site
            if site == insite:
                continue
            try:
                result[site] = pywikibot.Page(site, pagetitle, insite=insite)
            except pywikibot.InvalidTitle:
                pywikibot.output(u'[getLanguageLinks] Text contains invalid '
                                 u'interwiki link [[%s:%s]].'
                                 % (lang, pagetitle))
                continue
    return result


def removeLanguageLinks(text, site=None, marker=''):
    """Return text with all inter-language links removed.

    If a link to an unknown language is encountered, a warning is printed.
    If a marker is defined, that string is placed at the location of the
    last occurrence of an interwiki link (at the end if there are no
    interwiki links).

    """
    if site is None:
        site = pywikibot.Site()
    if not site.validLanguageLinks():
        return text
    # This regular expression will find every interwiki link, plus trailing
    # whitespace.
    languages = '|'.join(site.validLanguageLinks() +
                         list(site.family.obsolete.keys()))
    interwikiR = re.compile(r'\[\[(%s)\s?:[^\[\]\n]*\]\][\s]*'
                            % languages, re.IGNORECASE)
    text = replaceExcept(text, interwikiR, '',
                         ['nowiki', 'comment', 'math', 'pre', 'source'],
                         marker=marker,
                         site=site)
    return text.strip()


def removeLanguageLinksAndSeparator(text, site=None, marker='', separator=''):
    """
    Return text with inter-language links and preceding separators removed.

    If a link to an unknown language is encountered, a warning is printed.
    If a marker is defined, that string is placed at the location of the
    last occurrence of an interwiki link (at the end if there are no
    interwiki links).

    """
    if separator:
        mymarker = findmarker(text, u'@L@')
        newtext = removeLanguageLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    else:
        return removeLanguageLinks(text, site, marker)


def replaceLanguageLinks(oldtext, new, site=None, addOnly=False,
                         template=False, template_subpage=False):
    """Replace inter-language links in the text with a new set of links.

    'new' should be a dict with the Site objects as keys, and Page or Link
    objects as values (i.e., just like the dict returned by getLanguageLinks
    function).
    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    separator = site.family.interwiki_text_separator
    cseparator = site.family.category_text_separator
    separatorstripped = separator.strip()
    cseparatorstripped = cseparator.strip()
    do_not_strip = oldtext.strip() != oldtext
    if do_not_strip:
        issue_deprecation_warning('Using unstripped text', 'stripped text', 2)
    if addOnly:
        s2 = oldtext
    else:
        s2 = removeLanguageLinksAndSeparator(oldtext, site=site, marker=marker,
                                             separator=separatorstripped)
    s = interwikiFormat(new, insite=site)
    if s:
        if site.language() in site.family.interwiki_attop or \
           u'<!-- interwiki at top -->' in oldtext:
            # do not add separator if interwiki links are on one line
            newtext = s + (u'' if site.language()
                           in site.family.interwiki_on_one_line
                           else separator) + s2.replace(marker, '').strip()
        else:
            # calculate what was after the language links on the page
            firstafter = s2.find(marker)
            if firstafter < 0:
                firstafter = len(s2)
            else:
                firstafter += len(marker)
            # Any text in 'after' part that means we should keep it after?
            if "</noinclude>" in s2[firstafter:]:
                if separatorstripped:
                    s = separator + s
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            elif site.language() in site.family.categories_last:
                cats = getCategoryLinks(s2, site=site)
                s2 = removeCategoryLinksAndSeparator(
                    s2.replace(marker, cseparatorstripped).strip(), site) + \
                    separator + s
                newtext = replaceCategoryLinks(s2, cats, site=site,
                                               addOnly=True)
            # for Wikitravel's language links position.
            # (not supported by rewrite - no API)
            elif site.family.name == 'wikitravel':
                s = separator + s + separator
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            else:
                if template or template_subpage:
                    if template_subpage:
                        includeOn = '<includeonly>'
                        includeOff = '</includeonly>'
                    else:
                        includeOn = '<noinclude>'
                        includeOff = '</noinclude>'
                        separator = ''
                    # Do we have a noinclude at the end of the template?
                    parts = s2.split(includeOff)
                    lastpart = parts[-1]
                    if re.match(r'\s*%s' % marker, lastpart):
                        # Put the langlinks back into the noinclude's
                        regexp = re.compile(r'%s\s*%s' % (includeOff, marker))
                        newtext = regexp.sub(s + includeOff, s2)
                    else:
                        # Put the langlinks at the end, inside noinclude's
                        newtext = (s2.replace(marker, '').strip() +
                                   separator +
                                   u'%s\n%s%s\n' % (includeOn, s, includeOff)
                                   )
                else:
                    newtext = s2.replace(marker, '').strip() + separator + s
    else:
        newtext = s2.replace(marker, '')
    return newtext if do_not_strip else newtext.strip()


def interwikiFormat(links, insite=None):
    """Convert interwiki link dict into a wikitext string.

    @param links: interwiki links to be formatted
    @type links: dict with the Site objects as keys, and Page
        or Link objects as values.
    @param insite: site the interwiki links will be formatted for
        (defaulting to the current site).
    @type insite: BaseSite
    @return: string including wiki links formatted for inclusion
        in insite
    @rtype: unicode
    """
    if insite is None:
        insite = pywikibot.Site()
    if not links:
        return ''

    ar = interwikiSort(list(links.keys()), insite)
    s = []
    for site in ar:
        if isinstance(links[site], pywikibot.Link):
            links[site] = pywikibot.Page(links[site])
        if isinstance(links[site], pywikibot.Page):
            title = links[site].title(asLink=True, forceInterwiki=True,
                                      insite=insite)
            link = title.replace('[[:', '[[')
            s.append(link)
        else:
            raise ValueError('links dict must contain Page or Link objects')
    if insite.lang in insite.family.interwiki_on_one_line:
        sep = u' '
    else:
        sep = config.line_separator
    s = sep.join(s) + config.line_separator
    return s


def interwikiSort(sites, insite=None):
    """Sort sites according to local interwiki sort logic."""
    if not sites:
        return []
    if insite is None:
        insite = pywikibot.Site()

    sites.sort()
    putfirst = insite.interwiki_putfirst()
    if putfirst:
        # In this case I might have to change the order
        firstsites = []
        validlanglinks = insite.validLanguageLinks()
        for code in putfirst:
            if code in validlanglinks:
                site = insite.getSite(code=code)
                if site in sites:
                    del sites[sites.index(site)]
                    firstsites = firstsites + [site]
        sites = firstsites + sites
    if insite.interwiki_putfirst_doubled(sites):
        # some (all?) implementations return False
        sites = insite.interwiki_putfirst_doubled(sites) + sites
    return sites


# -------------------------------------
# Functions dealing with category links
# -------------------------------------

def getCategoryLinks(text, site=None, include=[], expand_text=False):
    """Return a list of category links found in text.

    @param include: list of tags which should not be removed by
        removeDisabledParts() and where CategoryLinks can be searched.
    @type include: list

    @return: all category links found
    @rtype: list of Category objects
    """
    result = []
    if site is None:
        site = pywikibot.Site()
    # Ignore category links within nowiki tags, pre tags, includeonly tags,
    # and HTML comments
    text = removeDisabledParts(text, include=include)
    catNamespace = '|'.join(site.category_namespaces())
    R = re.compile(r'\[\[\s*(?P<namespace>%s)\s*:\s*(?P<rest>.+?)\]\]'
                   % catNamespace, re.I)
    for match in R.finditer(text):
        if expand_text and '{{' in match.group('rest'):
            rest = site.expand_text(match.group('rest'))
        else:
            rest = match.group('rest')
        if '|' in rest:
            title, sortKey = rest.split('|', 1)
        else:
            title, sortKey = rest, None
        cat = pywikibot.Category(pywikibot.Link(
                                 '%s:%s' % (match.group('namespace'), title),
                                 site),
                                 sortKey=sortKey)
        result.append(cat)
    return result


def removeCategoryLinks(text, site=None, marker=''):
    """Return text with all category links removed.

    Put the string marker after the last replacement (at the end of the text
    if there is no replacement).
    """
    # This regular expression will find every link that is possibly an
    # interwiki link, plus trailing whitespace. The language code is grouped.
    # NOTE: This assumes that language codes only consist of non-capital
    # ASCII letters and hyphens.
    if site is None:
        site = pywikibot.Site()
    catNamespace = '|'.join(site.category_namespaces())
    categoryR = re.compile(r'\[\[\s*(%s)\s*:.*?\]\]\s*' % catNamespace, re.I)
    text = replaceExcept(text, categoryR, '',
                         ['nowiki', 'comment', 'math', 'pre', 'source', 'includeonly'],
                         marker=marker,
                         site=site)
    if marker:
        # avoid having multiple linefeeds at the end of the text
        text = re.sub(r'\s*%s' % re.escape(marker), config.LS + marker,
                      text.strip())
    return text.strip()


def removeCategoryLinksAndSeparator(text, site=None, marker='', separator=''):
    """
    Return text with all category links and preceding separators removed.

    Put the string marker after the last replacement (at the end of the text
    if there is no replacement).

    """
    if site is None:
        site = pywikibot.Site()
    if separator:
        mymarker = findmarker(text, u'@C@')
        newtext = removeCategoryLinks(text, site, mymarker)
        mymarker = expandmarker(newtext, mymarker, separator)
        return newtext.replace(mymarker, marker)
    else:
        return removeCategoryLinks(text, site, marker)


def replaceCategoryInPlace(oldtext, oldcat, newcat, site=None):
    """
    Replace old category with new one and return the modified text.

    @param oldtext: Content of the old category
    @param oldcat: pywikibot.Category object of the old category
    @param newcat: pywikibot.Category object of the new category
    @return: the modified text
    @rtype: unicode
    """
    if site is None:
        site = pywikibot.Site()

    catNamespace = '|'.join(site.category_namespaces())
    title = oldcat.title(withNamespace=False)
    if not title:
        return
    # title might contain regex special characters
    title = re.escape(title)
    # title might not be capitalized correctly on the wiki
    if title[0].isalpha() and site.namespaces[14].case == 'first-letter':
        title = "[%s%s]" % (title[0].upper(), title[0].lower()) + title[1:]
    # spaces and underscores in page titles are interchangeable and collapsible
    title = title.replace(r"\ ", "[ _]+").replace(r"\_", "[ _]+")
    categoryR = re.compile(r'\[\[\s*(%s)\s*:\s*%s\s*((?:\|[^]]+)?\]\])'
                           % (catNamespace, title), re.I)
    categoryRN = re.compile(
        r'^[^\S\n]*\[\[\s*(%s)\s*:\s*%s\s*((?:\|[^]]+)?\]\])[^\S\n]*\n'
        % (catNamespace, title), re.I | re.M)
    if newcat is None:
        # First go through and try the more restrictive regex that removes
        # an entire line, if the category is the only thing on that line (this
        # prevents blank lines left over in category lists following a removal.)
        text = replaceExcept(oldtext, categoryRN, '',
                             ['nowiki', 'comment', 'math', 'pre', 'source'],
                             site=site)
        text = replaceExcept(text, categoryR, '',
                             ['nowiki', 'comment', 'math', 'pre', 'source'],
                             site=site)
    else:
        text = replaceExcept(oldtext, categoryR,
                             '[[%s:%s\\2' % (site.namespace(14),
                                             newcat.title(withNamespace=False)),
                             ['nowiki', 'comment', 'math', 'pre', 'source'],
                             site=site)
    return text


def replaceCategoryLinks(oldtext, new, site=None, addOnly=False):
    """
    Replace all existing category links with new category links.

    @param oldtext: The text that needs to be replaced.
    @param new: Should be a list of Category objects or strings
        which can be either the raw name or [[Category:..]].
    @param addOnly: If addOnly is True, the old category won't be deleted and the
        category(s) given will be added (and so they won't replace anything).
    """
    # Find a marker that is not already in the text.
    marker = findmarker(oldtext)
    if site is None:
        site = pywikibot.Site()
    if site.sitename() == 'wikipedia:de' and "{{Personendaten" in oldtext:
        raise pywikibot.Error("""\
The Pywikibot is no longer allowed to touch categories on the German
Wikipedia on pages that contain the Personendaten template because of the
non-standard placement of that template.
See https://de.wikipedia.org/wiki/Hilfe_Diskussion:Personendaten/Archiv/1#Position_der_Personendaten_am_.22Artikelende.22
""")
    separator = site.family.category_text_separator
    iseparator = site.family.interwiki_text_separator
    separatorstripped = separator.strip()
    iseparatorstripped = iseparator.strip()
    if addOnly:
        s2 = oldtext
    else:
        s2 = removeCategoryLinksAndSeparator(oldtext, site=site, marker=marker,
                                             separator=separatorstripped)
    s = categoryFormat(new, insite=site)
    if s:
        if site.language() in site.family.category_attop:
            newtext = s + separator + s2
        else:
            # calculate what was after the categories links on the page
            firstafter = s2.find(marker)
            if firstafter < 0:
                firstafter = len(s2)
            else:
                firstafter += len(marker)
            # Is there text in the 'after' part that means we should keep it
            # after?
            if "</noinclude>" in s2[firstafter:]:
                if separatorstripped:
                    s = separator + s
                newtext = (s2[:firstafter].replace(marker, '') +
                           s +
                           s2[firstafter:])
            elif site.language() in site.family.categories_last:
                newtext = s2.replace(marker, '').strip() + separator + s
            else:
                interwiki = getLanguageLinks(s2, insite=site)
                s2 = removeLanguageLinksAndSeparator(s2.replace(marker, ''),
                                                     site, '',
                                                     iseparatorstripped
                                                     ) + separator + s
                newtext = replaceLanguageLinks(s2, interwiki, site=site,
                                               addOnly=True)
    else:
        newtext = s2.replace(marker, '')
    return newtext.strip()


def categoryFormat(categories, insite=None):
    """Return a string containing links to all categories in a list.

    'categories' should be a list of Category or Page objects or strings
    which can be either the raw name, [[Category:..]] or [[cat_localised_ns:...]].

    The string is formatted for inclusion in insite.
    Category namespace is converted to localised namespace.
    """
    if not categories:
        return ''
    if insite is None:
        insite = pywikibot.Site()

    catLinks = []
    for category in categories:
        if isinstance(category, basestring):
            category, separator, sortKey = category.strip('[]').partition('|')
            sortKey = sortKey if separator else None
            prefix = category.split(":", 1)[0]  # whole word if no ":" is present
            if prefix not in insite.namespaces[14]:
                category = u'{0}:{1}'.format(insite.namespace(14), category)
            category = pywikibot.Category(pywikibot.Link(category,
                                                         insite,
                                                         defaultNamespace=14),
                                          sortKey=sortKey)
        # Make sure a category is casted from Page to Category.
        elif not isinstance(category, pywikibot.Category):
            category = pywikibot.Category(category)
        link = category.aslink()
        catLinks.append(link)

    if insite.category_on_one_line():
        sep = ' '
    else:
        sep = config.line_separator
    # Some people don't like the categories sorted
    # catLinks.sort()
    return sep.join(catLinks) + config.line_separator


# -------------------------------------
# Functions dealing with external links
# -------------------------------------

def compileLinkR(withoutBracketed=False, onlyBracketed=False):
    """Return a regex that matches external links."""
    # RFC 2396 says that URLs may only contain certain characters.
    # For this regex we also accept non-allowed characters, so that the bot
    # will later show these links as broken ('Non-ASCII Characters in URL').
    # Note: While allowing dots inside URLs, MediaWiki will regard
    # dots at the end of the URL as not part of that URL.
    # The same applies to comma, colon and some other characters.
    notAtEnd = r'\]\s\.:;,<>"\|\)'
    # So characters inside the URL can be anything except whitespace,
    # closing squared brackets, quotation marks, greater than and less
    # than, and the last character also can't be parenthesis or another
    # character disallowed by MediaWiki.
    notInside = r'\]\s<>"'
    # The first half of this regular expression is required because '' is
    # not allowed inside links. For example, in this wiki text:
    #       ''Please see https://www.example.org.''
    # .'' shouldn't be considered as part of the link.
    regex = r'(?P<url>http[s]?://[^%(notInside)s]*?[^%(notAtEnd)s]' \
            r'(?=[%(notAtEnd)s]*\'\')|http[s]?://[^%(notInside)s]*' \
            r'[^%(notAtEnd)s])' % {'notInside': notInside, 'notAtEnd': notAtEnd}

    if withoutBracketed:
        regex = r'(?<!\[)' + regex
    elif onlyBracketed:
        regex = r'\[' + regex
    linkR = re.compile(regex)
    return linkR


# --------------------------------
# Functions dealing with templates
# --------------------------------

def extract_templates_and_params(text):
    """Return a list of templates found in text.

    Return value is a list of tuples. There is one tuple for each use of a
    template in the page, with the template title as the first entry and a
    dict of parameters as the second entry.  Parameters are indexed by
    strings; as in MediaWiki, an unnamed parameter is given a parameter name
    with an integer value corresponding to its position among the unnamed
    parameters, and if this results multiple parameters with the same name
    only the last value provided will be returned.

    This uses the package L{mwparserfromhell} (mwpfh) if it is installed
    and enabled by config.mwparserfromhell. Otherwise it falls back on a
    regex based implementation.

    There are minor differences between the two implementations.

    The two implementations return nested templates in a different order.
    i.e. for {{a|b={{c}}}}, mwpfh returns [a, c], whereas regex returns [c, a].

    mwpfh preserves whitespace in parameter names and values.  regex excludes
    anything between <!-- --> before parsing the text.

    @param text: The wikitext from which templates are extracted
    @type text: unicode or string
    @return: list of template name and params
    @rtype: list of tuple
    """
    use_mwparserfromhell = config.use_mwparserfromhell
    if use_mwparserfromhell:
        try:
            import mwparserfromhell  # noqa
        except ImportError:
            use_mwparserfromhell = False

    if use_mwparserfromhell:
        return extract_templates_and_params_mwpfh(text)
    else:
        return extract_templates_and_params_regex(text)


def extract_templates_and_params_mwpfh(text):
    """
    Extract templates with params using mwparserfromhell.

    This function should not be called directly.

    Use extract_templates_and_params, which will select this
    mwparserfromhell implementation if based on whether the
    mwparserfromhell package is installed and enabled by
    config.mwparserfromhell.

    @param text: The wikitext from which templates are extracted
    @type text: unicode or string
    @return: list of template name and params
    @rtype: list of tuple
    """
    import mwparserfromhell
    code = mwparserfromhell.parse(text)
    result = []
    for template in code.filter_templates(recursive=True):
        params = OrderedDict()
        for param in template.params:
            params[unicode(param.name)] = unicode(param.value)
        result.append((unicode(template.name.strip()), params))
    return result


def extract_templates_and_params_regex(text):
    """
    Extract templates with params using a regex.

    This function should not be called directly.

    Use extract_templates_and_params, which will fallback to using this
    regex based implementation when the mwparserfromhell implementation
    is not used.

    @param text: The wikitext from which templates are extracted
    @type text: unicode or string
    @return: list of template name and params
    @rtype: list of tuple
    """
    # remove commented-out stuff etc.
    thistxt = removeDisabledParts(text)

    # marker for inside templates or parameters
    marker1 = findmarker(thistxt)

    # marker for links
    marker2 = findmarker(thistxt, u'##', u'#')

    # marker for math
    marker3 = findmarker(thistxt, u'%%', u'%')

    # marker for value parameter
    marker4 = findmarker(thistxt, u'§§', u'§')

    result = []
    Rmath = re.compile(r'<math>[^<]+</math>')
    Rvalue = re.compile(r'{{{.+?}}}')
    Rmarker1 = re.compile(r'%s(\d+)%s' % (marker1, marker1))
    Rmarker2 = re.compile(r'%s(\d+)%s' % (marker2, marker2))
    Rmarker3 = re.compile(r'%s(\d+)%s' % (marker3, marker3))
    Rmarker4 = re.compile(r'%s(\d+)%s' % (marker4, marker4))

    # Replace math with markers
    maths = {}
    count = 0
    for m in Rmath.finditer(thistxt):
        count += 1
        item = m.group()
        thistxt = thistxt.replace(item, '%s%d%s' % (marker3, count, marker3))
        maths[count] = item

    values = {}
    count = 0
    for m in Rvalue.finditer(thistxt):
        count += 1
        # If we have digits between brackets, restoring from dict may fail.
        # So we need to change the index. We have to search in the origin text.
        while u'}}}%d{{{' % count in text:
            count += 1
        item = m.group()
        thistxt = thistxt.replace(item, '%s%d%s' % (marker4, count, marker4))
        values[count] = item

    inside = {}
    seen = set()
    count = 0
    while TEMP_REGEX.search(thistxt) is not None:
        for m in TEMP_REGEX.finditer(thistxt):
            # Make sure it is not detected again
            item = m.group()
            if item in seen:
                continue  # speed up
            seen.add(item)
            count += 1
            while u'}}%d{{' % count in text:
                count += 1
            thistxt = thistxt.replace(item,
                                      '%s%d%s' % (marker1, count, marker1))

            # Make sure stored templates don't contain markers
            for m2 in Rmarker1.finditer(item):
                item = item.replace(m2.group(), inside[int(m2.group(1))])
            for m2 in Rmarker3.finditer(item):
                item = item.replace(m2.group(), maths[int(m2.group(1))])
            for m2 in Rmarker4.finditer(item):
                item = item.replace(m2.group(), values[int(m2.group(1))])
            inside[count] = item

            # Name
            name = m.group('name').strip()
            m2 = Rmarker1.search(name) or Rmath.search(name)
            if m2 is not None:
                # Doesn't detect templates whose name changes,
                # or templates whose name contains math tags
                continue

            # {{#if: }}
            if not name or name.startswith('#'):
                continue

# TODO: implement the following; 'self' and site dont exist in this function
#            if self.site().isInterwikiLink(name):
#                continue
#            # {{DEFAULTSORT:...}}
#            from pywikibot.tools import MediaWikiVersion
#            defaultKeys = MediaWikiVersion(self.site.version()) > MediaWikiVersion("1.13") and \
#                          self.site().getmagicwords('defaultsort')
#            # It seems some wikis does not have this magic key
#            if defaultKeys:
#                found = False
#                for key in defaultKeys:
#                    if name.startswith(key):
#                        found = True
#                        break
#                if found: continue
#
#            try:
#                name = Page(self.site(), name).title()
#            except InvalidTitle:
#                if name:
#                    output(
#                        u"Page %s contains invalid template name {{%s}}."
#                       % (self.title(), name.strip()))
#                continue

            # Parameters
            paramString = m.group('params')
            params = OrderedDict()
            numbered_param = 1
            if paramString:
                # Replace wikilinks with markers
                links = {}
                count2 = 0
                for m2 in pywikibot.link_regex.finditer(paramString):
                    count2 += 1
                    item = m2.group(0)
                    paramString = paramString.replace(
                        item, '%s%d%s' % (marker2, count2, marker2))
                    links[count2] = item
                # Parse string
                markedParams = paramString.split('|')
                # Replace markers
                for param in markedParams:
                    if "=" in param:
                        param_name, param_val = param.split("=", 1)
                    else:
                        param_name = unicode(numbered_param)
                        param_val = param
                        numbered_param += 1
                    count = len(inside)
                    for m2 in Rmarker1.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      inside[int(m2.group(1))])
                    for m2 in Rmarker2.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      links[int(m2.group(1))])
                    for m2 in Rmarker3.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      maths[int(m2.group(1))])
                    for m2 in Rmarker4.finditer(param_val):
                        param_val = param_val.replace(m2.group(),
                                                      values[int(m2.group(1))])
                    params[param_name.strip()] = param_val.strip()

            # Add it to the result
            result.append((name, params))
    return result


def glue_template_and_params(template_and_params):
    """Return wiki text of template glued from params.

    You can use items from extract_templates_and_params here to get
    an equivalent template wiki text (it may happen that the order
    of the params changes).
    """
    (template, params) = template_and_params
    text = u''
    for item in params:
        text += u'|%s=%s\n' % (item, params[item])

    return u'{{%s\n%s}}' % (template, text)


# --------------------------
# Page parsing functionality
# --------------------------

def does_text_contain_section(pagetext, section):
    """
    Determine whether the page text contains the given section title.

    It does not care whether a section string may contain spaces or
    underlines. Both will match.

    If a section parameter contains a internal link, it will match the
    section with or without a preceding colon which is required for a
    text link e.g. for categories and files.

    @param pagetext: The wikitext of a page
    @type pagetext: unicode or string
    @param section: a section of a page including wikitext markups
    @type section: unicode or string

    """
    # match preceding colon for text links
    section = re.sub(r'\\\[\\\[(\\:)?', r'\[\[\:?', re.escape(section))
    # match underscores and white spaces
    section = re.sub(r'\\?[ _]', '[ _]', section)
    m = re.search("=+[ ']*%s[ ']*=+" % section, pagetext)
    return bool(m)


def reformat_ISBNs(text, match_func):
    """Reformat ISBNs.

    @param text: text containing ISBNs
    @type text: str
    @param match_func: function to reformat matched ISBNs
    @type match_func: callable
    @return: reformatted text
    @rtype: str
    """
    isbnR = re.compile(r'(?<=ISBN )(?P<code>[\d\-]+[\dXx])')
    text = isbnR.sub(match_func, text)
    return text


# ---------------------------------------
# Time parsing functionality (Archivebot)
# ---------------------------------------

class tzoneFixedOffset(datetime.tzinfo):

    """
    Class building tzinfo objects for fixed-offset time zones.

    @param offset: a number indicating fixed offset in minutes east from UTC
    @param name: a string with name of the timezone
    """

    def __init__(self, offset, name):
        """Constructor."""
        self.__offset = datetime.timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        """Return the offset to UTC."""
        return self.__offset

    def tzname(self, dt):
        """Return the name of the timezone."""
        return self.__name

    def dst(self, dt):
        """Return no daylight savings time."""
        return datetime.timedelta(0)

    def __repr__(self):
        """Return the internal representation of the timezone."""
        return "%s(%s, %s)" % (
            self.__class__.__name__,
            self.__offset.days * 86400 + self.__offset.seconds,
            self.__name
        )


class TimeStripper(object):

    """Find timestamp in page and return it as timezone aware datetime object."""

    def __init__(self, site=None):
        """Constructor."""
        if site is None:
            self.site = pywikibot.Site()
        else:
            self.site = site

        self.origNames2monthNum = {}
        for n, (_long, _short) in enumerate(self.site.months_names, start=1):
            self.origNames2monthNum[_long] = n
            self.origNames2monthNum[_short] = n
            # in some cases month in ~~~~ might end without dot even if
            # site.months_names do not.
            if _short.endswith('.'):
                self.origNames2monthNum[_short[:-1]] = n

        self.groups = [u'year', u'month',  u'hour',  u'time', u'day', u'minute', u'tzinfo']

        timeR = r'(?P<time>(?P<hour>([0-1]\d|2[0-3]))[:\.h](?P<minute>[0-5]\d))'
        timeznR = r'\((?P<tzinfo>[A-Z]+)\)'
        yearR = r'(?P<year>(19|20)\d\d)(?:%s)?' % u'\ub144'
        # if months have 'digits' as names, they need to be
        # removed; will be handled as digits in regex, adding d+{1,2}\.?
        escaped_months = [_ for _ in self.origNames2monthNum if
                          not _.strip('.').isdigit()]
        # match longest names first.
        escaped_months = [re.escape(_) for
                          _ in sorted(escaped_months, reverse=True)]
        # work around for cs wiki: if month are in digits, we assume
        # that format is dd. mm. (with dot and spaces optional)
        # the last one is workaround for Korean
        if any(_.isdigit() for _ in self.origNames2monthNum):
            self.is_digit_month = True
            monthR = r'(?P<month>(%s)|(?:1[012]|0?[1-9])\.)' \
                % u'|'.join(escaped_months)
            dayR = r'(?P<day>(3[01]|[12]\d|0?[1-9]))(?:%s)?\.?\s*(?:[01]?\d\.)?' % u'\uc77c'
        else:
            self.is_digit_month = False
            monthR = r'(?P<month>(%s))' % u'|'.join(escaped_months)
            dayR = r'(?P<day>(3[01]|[12]\d|0?[1-9]))\.?'

        self.ptimeR = re.compile(timeR)
        self.ptimeznR = re.compile(timeznR)
        self.pyearR = re.compile(yearR)
        self.pmonthR = re.compile(monthR)
        self.pdayR = re.compile(dayR)

        # order is important to avoid mismatch when searching
        self.patterns = [
            self.ptimeR,
            self.ptimeznR,
            self.pyearR,
            self.pmonthR,
            self.pdayR,
        ]

        self.linkP = compileLinkR()
        self.comment_pattern = re.compile(r'<!--(.*?)-->')

        self.tzinfo = tzoneFixedOffset(self.site.siteinfo['timeoffset'],
                                       self.site.siteinfo['timezone'])

    def findmarker(self, text, base=u'@@', delta='@'):
        """Find a string which is not part of text."""
        while base in text:
            base += delta
        return base

    def fix_digits(self, line):
        """Make non-latin digits like Persian to latin to parse."""
        for system in NON_LATIN_DIGITS.values():
            for i in range(0, 10):
                line = line.replace(system[i], str(i))
        return line

    def last_match_and_replace(self, txt, pat):
        """
        Take the rightmost match and replace with marker.

        It does so to prevent spurious earlier matches.
        """
        m = None
        cnt = 0
        for m in pat.finditer(txt):
            cnt += 1

        if m:
            marker = self.findmarker(txt)
            # month and day format might be identical (e.g. see bug 69315),
            # avoid to wipe out day, after month is matched.
            # replace all matches but the last two
            # (i.e. allow to search for dd. mm.)
            if pat == self.pmonthR:
                if self.is_digit_month:
                    if cnt > 2:
                        txt = pat.sub(marker, txt, cnt - 2)
                else:
                    txt = pat.sub(marker, txt)
            else:
                txt = pat.sub(marker, txt)
            return (txt, m.groupdict())
        else:
            return (txt, None)

    def timestripper(self, line):
        """
        Find timestamp in line and convert it to time zone aware datetime.

        All the following items must be matched, otherwise None is returned:
        -. year, month, hour, time, day, minute, tzinfo
        """
        # match date fields
        dateDict = dict()
        # Analyze comments separately from rest of each line to avoid to skip
        # dates in comments, as the date matched by timestripper is the
        # rightmost one.
        most_recent = []
        for comment in self.comment_pattern.finditer(line):
            # Recursion levels can be maximum two. If a comment is found, it will
            # not for sure be found in the next level.
            # Nested cmments are excluded by design.
            timestamp = self.timestripper(comment.group(1))
            most_recent.append(timestamp)

        # Remove parts that are not supposed to contain the timestamp, in order
        # to reduce false positives.
        line = removeDisabledParts(line)
        line = self.linkP.sub('', line)  # remove external links

        line = self.fix_digits(line)
        for pat in self.patterns:
            line, matchDict = self.last_match_and_replace(line, pat)
            if matchDict:
                dateDict.update(matchDict)

        # all fields matched -> date valid
        if all(g in dateDict for g in self.groups):
            # remove 'time' key, now split in hour/minute and not needed by datetime
            del dateDict['time']

            # replace month name in original language with month number
            try:
                dateDict['month'] = self.origNames2monthNum[dateDict['month']]
            except KeyError:
                pywikibot.output(u'incorrect month name "%s" in page in site %s'
                                 % (dateDict['month'], self.site))
                raise KeyError

            # convert to integers
            for k, v in dateDict.items():
                if k == 'tzinfo':
                    continue
                try:
                    dateDict[k] = int(v)
                except ValueError:
                    raise ValueError('Value: %s could not be converted for key: %s.'
                                     % (v, k))

            # find timezone
            dateDict['tzinfo'] = self.tzinfo

            timestamp = datetime.datetime(**dateDict)
        else:
            timestamp = None

        most_recent.append(timestamp)

        try:
            timestamp = max(ts for ts in most_recent if ts is not None)
        except ValueError:
            timestamp = None

        return timestamp
