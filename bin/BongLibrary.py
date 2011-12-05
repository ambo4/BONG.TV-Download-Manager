"""
A collection of various utility functions
"""
import re
import htmlentitydefs


def unicode_string(param, encoding='utf-8'):
    """
    convert a byte string to unicode
    """
    if isinstance(param, basestring):
        if isinstance(param, str):
            param = param.decode(encoding)
    return param

def utf8_string(param):
    """
    convert a unicode string to a byte string using the UTF-8 encoding
    """
    if isinstance(param, basestring):
        if isinstance(param, unicode):
            param = param.encode('utf-8')
    return param

def unescape(text):
    """
    Removes HTML or XML character references and entities from a text string.
    
    @param text The HTML (or XML) source text.
    @return The plain text, as a Unicode string, if necessary.
    
    Author: Fredrik Lundh (http://effbot.org/zone/re-sub.htm#unescape-html)
    """
    if isinstance(text, basestring):
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text # leave as is
        return re.sub("&#?\w+;", fixup, text)
    else:
        return text

def alignMultipleTextLines(text):
    """
    Remove leading whitespace from multi-line strings
    
    Docstrings like this one are indented in source text
    for readability. This extra whitespace has to be
    removed before the string is written to other output
    """
    tl = text.splitlines()
    
    # remove leading empty lines
    a = 0
    while a < len(tl):
        if tl[a].lstrip() == "":
            a += 1
        else:
            break
    
    # remove trailing empty lines
    e = len(tl)-1
    while a <= e:
        if tl[e].lstrip() == "":
            e -= 1
        else:
            break
    
    # return empty string if only empty lines found
    if e < a:
        return ""
    
    # slice content lines
    tl = tl[a:e+1]    
    
    # short cut if only a single content line found
    if 1 == len(tl):
        return tl[0].lstrip() + '\n'
        
    # first lines indentation determines left alignment 
    
    # the pattern ^(\s*)(.*)$ always matches with 
    # possibly empty submatches [1] for leading whitespace
    # and [2] for the remainder of the line
    pattern = re.compile("^(\s*)(.*)$")
    matches = pattern.match(tl[0])
    prefirst = matches.group(1)
    
    if prefirst == "":
        # if the first line has no indentation, there is 
        # nothing more to do. Just return the lines.
        return "\n".join(tl) + "\n"
    else:
        # throw first lines leading whitespace away
        tl[0] = matches.group(2)
 
    # remove first lines whitepace from all
    # consecutive lines of text
    for i in xrange(1, len(tl)):
        matches = pattern.match(tl[i])
        pre = matches.group(1)
        p = 0
        while p < min(len(prefirst), len(pre)):
            if prefirst[p] == pre[p]:
                p += 1
            else:
                break
        if p < len(pre):
            tl[i] = pre[p:] + matches.group(2)
        else:
            tl[i] = matches.group(2)

    return "\n".join(tl) + "\n"


def leadZero(txt, len=2):
    return txt.rjust(len, "0")
    
def renameResource(url, basename):
    l = url.split('.')
    return basename + '.' + l[-1]

def bongDateTimeToSqlite(bts, default=None):
    pattern = re.compile("^([0-3]?[0-9])-([0-1]?[0-9])-(2[0-9]{3}) ([0-2]?[0-9]):([0-5]?[0-9])$")
    m = pattern.match(bts)
    if m:
        day = leadZero(m.group(1))
        month = leadZero(m.group(2)) 
        year = leadZero(m.group(3))
        hour = leadZero(m.group(4))
        minute = leadZero(m.group(5))
        return "{}-{}-{} {}:{}:00".format(year, month, day, hour, minute)
    else:
        return default

def bongTimeToSqlite(bts, default=None):
    pattern = re.compile("^([0-2]?[0-9]):([0-5]?[0-9])$")
    m = pattern.match(bts)
    if m:
        hour = leadZero(m.group(1))
        minute = leadZero(m.group(2))
        return "{}:{}:00".format(hour, minute)
    else:
        return default


