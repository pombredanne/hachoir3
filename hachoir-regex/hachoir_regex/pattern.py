from hachoir_regex import RegexEmpty, RegexOr, parse, createString
from hachoir_regex.tools import makePrintable

class Pattern:
    def __init__(self, user):
        self.user = user

class StringPattern(Pattern):
    def __init__(self, text, user=None):
        Pattern.__init__(self, user)
        self.text = text

    def __str__(self):
        return makePrintable(self.text, 'ASCII', to_unicode=True)

    def __repr__(self):
        return "<StringPattern '%s'>" % self

class RegexPattern(Pattern):
    def __init__(self, regex, user=None):
        Pattern.__init__(self, user)
        self.regex = parse(regex)
        self._compiled_regex = None

    def __str__(self):
        return makePrintable(str(self.regex), 'ASCII', to_unicode=True)

    def __repr__(self):
        return "<RegexPattern '%s'>" % self

    def match(self, data):
        return self.compiled_regex.match(data)

    def _getCompiledRegex(self):
        if self._compiled_regex is None:
            self._compiled_regex = self.regex.compile(python=True)
        return self._compiled_regex
    compiled_regex = property(_getCompiledRegex)

class PatternMatching:
    """
    Fast pattern matching class.

    Create your patterns:

    >>> p=PatternMatching()
    >>> p.addString("a")
    >>> p.addString("b")
    >>> p.addRegex("[cd]e")

    Search patterns:

    >>> for item in p.search("a b ce"):
    ...    print item
    ...
    (0, 1, <StringPattern 'a'>)
    (2, 3, <StringPattern 'b'>)
    (4, 6, <RegexPattern '[cd]e'>)
    """
    def __init__(self):
        self.string_patterns = []
        self.string_dict = {}
        self.regex_patterns = []
        self._need_commit = True

    def commit(self):
        self._need_commit = False
        length = 0
        regex = None
        for item in self.string_patterns:
            if regex:
                regex |= createString(item.text)
            else:
                regex = createString(item.text)
            length = max(length, len(item.text))
        for item in self.regex_patterns:
            if regex:
                regex |= item.regex
            else:
                regex = item.regex
            length = max(length, item.regex.maxLength())
        if not regex:
            regex = RegexEmpty()
        self.regex = regex
        self.compiled_regex = regex.compile(python=True)
        self.max_length = length

    def addString(self, magic, user=None):
        item = StringPattern(magic, user)
        if item.text not in self.string_dict:
            self.string_patterns.append(item)
            self.string_dict[item.text] = item
            self._need_commit = True
        else:
            text = makePrintable(item.text, "ASCII", to_unicode=True)
            #warning("Skip duplicate string pattern (%s)" % text)

    def addRegex(self, regex, user=None):
        item = RegexPattern(regex, user)
        if item.regex.maxLength() is not None:
            self.regex_patterns.append(item)
            self._need_commit = True
        else:
            regex = makePrintable(str(item.regex), 'ASCII', to_unicode=True)
            #warning("Skip invalid regex pattern (%s)" % regex)

    def getPattern(self, data):
        """
        Get pattern item matching data.
        Raise KeyError if no pattern does match it.
        """
        # Try in string patterns
        try:
            return self.string_dict[data]
        except KeyError:
            pass

        # Try in regex patterns
        for item in self.regex_patterns:
            if item.match(data):
                return item
        raise KeyError("Unable to get pattern item")

    def search(self, data):
        """
        Search patterns in data.
        Return a generator of tuples: (start, end, item)
        """
        if self._need_commit:
            self.commit()
        for match in self.compiled_regex.finditer(data):
            item = self.getPattern(match.group(0))
            yield (match.start(0), match.end(0), item)

    def __str__(self):
        return makePrintable(str(self.regex), 'ASCII', to_unicode=True)

if __name__ == "__main__":
    import doctest, sys
    failure, nb_test = doctest.testmod()
    if failure:
        sys.exit(1)
