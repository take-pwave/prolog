class TokenType:
    def __init__(self, name):
        self.name = name
    
    def __eq__(self, tt):
        return self.name == tt.name

    def __ne__(self, tt):
        return not self.__eq__(tt)
    
class Token:
    EOF = None
    TT_EOF = TokenType("eof")
    TT_NUMBER = TokenType("number")
    TT_WORD = TokenType("word")
    TT_SYMBOL = TokenType("symbol")
    TT_QUOTED = TokenType("quoted")

    def __new__(cls, *args, **kargs):
        if cls.EOF == None:
            cls.EOF = super(Token, cls).__new__(cls)
            cls.EOF.ttype = Token.TT_EOF
            cls.EOF.name = ""
            cls.EOF.sval = 0
        return super(Token, cls).__new__(cls)
    
    def __init__(self, *args):
        self.sval = None
        self.nval = None
        if len(args) == 1:
            arg = args[0]
            self.sval = ""
            self.nval = 0
            if isinstance(arg, str):
                if len(arg) == 1:
                    self.ttype = Token.TT_SYMBOL
                else:
                    self.ttype = Token.TT_WORD
                self.sval = arg
            elif isinstance(arg, int) or isinstance(arg, float):
                self.ttype = Token.TT_NUMBER
                self.nval = arg
        elif len(args) == 3:
            self.ttype = args[0]
            self.sval = args[1]
            self.nval = args[2]

    def __eq__(self, o):
        if not isinstance(o, Token):
            return False
        t = o
        if self.ttype != t.ttype:
            return False
        if (self.ttype == Token.TT_NUMBER):
            return self.nval == t.nval
        if self.sval == None or t.sval == None:
            return False
        return self.sval == t.sval
    
    def equalsIgnoreCase(self, o):
        if self.ttype != Token.TT_NUMBER:
            t = o
            return self.sval.lower() == t.sval.lower()
        else:
            return False
    
    def isNumber(self):
        return self.ttype == Token.TT_NUMBER
    
    def isQuotedString(self):
        return self.ttype == Token.TT_QUOTED
    
    def isSymbol(self):
        return self.ttype == Token.TT_SYMBOL
    
    def isWord(self):
        return self.ttype == Token.TT_WORD
    
    def nval(self):
        return self.nval
    
    def sval(self):
        return self.sval
    
    def __str__(self):
        if self.ttype == Token.TT_EOF:
            return "EOF"
        return str(self.value())
    
    def value(self):
        if self.ttype == Token.TT_NUMBER:
            return str(self.nval)
        if self.ttype == Token.TT_EOF:
            return Token.EOF
        if self.sval != None:
            return self.sval

import io
import copy

class PushbackReader:
    def __init__(self, s):
        self.peek = None
        self.f = io.StringIO(s)
        if len(s) > 0:
            self.peek = self.f.read(1)
        
    def read(self):
        if self.peek != None:
            c = self.peek
            self.peek = None
            return c
        else:
            c = self.f.read(1)
            if len(c) == 1:
                return c
            else:
                return None
        
    def unread(self, c):
        self.peek = c


class NumberState:
    def __init__(self):
        self.c = None
        self._value = 0
        self.absorbedLeadingMinus = False
        self.absorbedDot = False
        self.gotAdigit = False
    
    def absorbDigits(self, r, fraction):
        divideBy = 1
        v = 0
        while(self.c != None and '0' <= self.c and self.c <= '9'):
            self.gotAdigit = True
            v = v*10 + (ord(self.c) - ord('0'))
            self.c = r.read()
            if fraction:
                divideBy *= 10
        if fraction:
            v = v / divideBy
        return v

    def nextToken(self, r, cin, t):
        self.reset(cin)
        self.parseLeft(r)
        self.parseRight(r)
        r.unread(self.c)
        return self.value(r, t)
    
    def parseLeft(self, r):
        if self.c == '-':
            self.c = r.read()
            self.absorbedLeadingMinus = True
        self._value = self.absorbDigits(r, False)

    def parseRight(self, r):
        if self.c == '.':
            self.c = r.read()
            self.absorbedDot = True
            self._value += self.absorbDigits(r, True)
    
    def reset(self, cin):
        self.c = cin
        self._value = 0
        self.absorbedLeadingMinus = False
        self.absorbedDot = False
        self.gotAdigit = False

    def value(self, r, t):
        if not self.gotAdigit:
            if self.absorbedLeadingMinus and self.absorbedDot:
                r.unread('.')
                return t.symbolState.nextToken(r, '-', t)
            if self.absorbedLeadingMinus:
                return t.symbolState.nextToken(r, '-', t)
            if self.absorbedDot:
                return t.symbolState.nextToken(r, '.', t)
        if self.absorbedLeadingMinus:
            self._value = -self._value
        return Token(Token.TT_NUMBER, "", self._value)

class QuoteState:
    def __init__(self):
        self.charbuf = [None for i in range(16)]
    
    def checkBufLength(self, i):
        if i >= len(self.charbuf):
            nb = [None for i in range(len(self.charbuf))]
            self.charbuf.extend(nb)

    def nextToken(self, r, cin, t):
        i = 0
        self.charbuf[i] = cin; i += 1
        c = None
        while True:
            c = r.read()
            if c == None:
                c = cin
            self.checkBufLength(i)
            self.charbuf[i] = c; i += 1
            if c == cin:
                break
        sval = ""
        for j in range(i):
            sval += self.charbuf[j]
        return Token(Token.TT_QUOTED, sval, 0)

class SlashSlashState:
    def nextToken(self, r, theSlash, t):
        c = None
        while True:
            c = r.read()
            if c == None or c == '\n' or c == '\r':
                break
        return t.nextToken()

class SlashStarState:
    def nextToken(self, r, theStar, t):
        c = None
        lastc = None
        while True:
            if lastc == '*' and c == '/':
                break
            lastc = c
            c = r.read()
            if c == None:
                break
        return t.nextToken()
    
class SlashState:
    def __init__(self):
        self.slashStarState = SlashStarState()
        self.slashSlashState = SlashSlashState()

    def nextToken(self, r, theSlash, t):
        c = r.read()
        if c == '*':
            return self.slashStarState.nextToken(r, '*', t)
        if c == '/':
            return self.slashSlashState.nextToken(r, '/', t)
        if c != None:
            r.unread(c)
        return Token(Token.TT_SYMBOL, "/", 0)


class SymbolNode:
    def __init__(self, parent, myChar):
        self.myChar = myChar
        self.parent = parent
        self.children = []
        self.valid = False

    def addDescendantLine(self, s):
        if len(s) > 0:
            c = s[0:1]
            n = self.ensureChildWithChar(c)
            n.addDescendantLine(s[1:len(s)])
    
    def ancestry(self):
        return self.parent.ancestry() + self.myChar
    
    def deepestRead(self, r):
        c = r.read()
        n = self.findChildWithChar(c)
        if n == None:
            r.unread(c)
            return self
        return n.deepestRead(r)

    def ensureChildWithChar(self, c):
        n = self.findChildWithChar(c)
        if n == None:
            n = SymbolNode(self, c)
            self.children.append(n)
        return n
    
    def findChildWithChar(self, c):
        for n in self.children:
            if n.myChar == c:
                return n
        return None
    
    def findDescendant(self, s):
        c = s[0:1]
        n = self.findChildWithChar(c)
        if len(s) == 1:
            return n
        return n.findDescendant(s[1:len(s)])
    
    def setValid(self, b):
        self.valid = b
    
    def __str__(self):
        return "" + self.myChar + '()' + self.valid + ')'
    
    def unreadToValid(self, r):
        if self.valid:
            return self
        r.unread(self.myChar)
        return self.parent.unreadToValid(r)
    
class SymbolRootNode(SymbolNode):
    def __init__(self):
        super().__init__(None, None)
        self.children = [None for i in range(256)]
        self.init()
    
    def add(self, s):
        c = s[0:1]
        n = self.ensureChildWithChar(c)
        n.addDescendantLine(s[1:len(s)])
        self.findDescendant(s).setValid(True)

    def ancestry(self):
        return ""
    
    def findChildWithChar(self, c):
        return self.children[ord(c)]
    
    def init(self):
        for i in range(len(self.children)):
            self.children[i] = SymbolNode(self, chr(i))
            self.children[i].setValid(True)
    
    def nextSymbol(self, r, first):
        n1 = self.findChildWithChar(first)
        n2 = n1.deepestRead(r)
        n3 = n2.unreadToValid(r)
        return n3.ancestry()
            
class SymbolState:
    def __init__(self):
        self.symbols = SymbolRootNode()
        self.add("!=")
        self.add(":-")
        self.add("<=")
        self.add(">=")

    def add(self, s):
        self.symbols.add(s)

    def nextToken(self, r, first, t):
        s = self.symbols.nextSymbol(r, first)
        return Token(Token.TT_SYMBOL, s, 0)

class WordState:
    def __init__(self):
        self.charbuf = [None for i in range(16)]
        self._wordChar = [False for i in range(256)]
        self.setWordChars('a', 'z', True)
        self.setWordChars('A', 'Z', True)
        self.setWordChars('0', '9', True)
        self.setWordChars('-', '-', True)
        self.setWordChars('_', '_', True)
        self.setWordChars("'", "'", True)
        self.setWordChars(chr(0xc0), chr(0xff), True)

    def checkBufLength(self, i):
        if i >= len(self.charbuf):
            nb = [None for i in range(len(self.charbuf))]
            self.charbuf.extend(nb)

    def nextToken(self, r, c, t):
        i = 0
        while True:
            self.checkBufLength(i)
            self.charbuf[i] = c; i += 1
            c = r.read()
            result = self.wordChar(c)
            if not result:
                break
        if not c == None:
            r.unread(c)
        sval = ""
        for j in range(i):
            sval += self.charbuf[j]
        return Token(Token.TT_WORD, sval, 0)
    
    def setWordChars(self, fromC, toC, b):
        fromI = ord(fromC)
        toI = ord(toC)
        for i in range(fromI, toI+1):
            self._wordChar[i] = b
    
    def wordChar(self, c):
        if c != None and ord(c) >= 0 and ord(c) < len(self._wordChar):
            return self._wordChar[ord(c)]
        return False

class WhitespaceState:
    def __init__(self):
        self.whitespaceChar = [False for i in range(256)]
        self.setWhitespaceChars(0, ord(' '), True)
    
    def nextToken(self, r, aWhitespaceChar, t):
        c = None
        while True:
            c = r.read()
            if c == None or ord(c) >= len(self.whitespaceChar) or not self.whitespaceChar[ord(c)]:
                break
        if c != None:
            r.unread(c)
        return t.nextToken()

    def setWhitespaceChars(self, fromI, toI, b):
        for i in range(fromI, toI+1):
            if i >= 0:
                self.whitespaceChar[i] = b

class Tokenizer:
    DEFAULT_SYMBOL_MAX = 4
    def __init__(self, *args):
        self.reader = None
        self.characterState = [None for i in range(256)]
        self.numberState = NumberState()
        self.quoteState = QuoteState()
        self.slashState = SlashState()
        self.symbolState = SymbolState()
        self.whitespaceState = WhitespaceState()
        self.wordState = WordState()
    
        # defaultState
        self.setCharacterState(0, 255, self.symbolState)
        # other state
        self.setCharacterState(0, ord(' '), self.whitespaceState)
        self.setCharacterState(ord('a'), ord('z'), self.wordState)
        self.setCharacterState(ord('A'), ord('Z'), self.wordState)
        self.setCharacterState(0xc0, 0xff, self.wordState)
        self.setCharacterState(ord('0'), ord('9'), self.numberState)
        self.setCharacterState(ord('-'), ord('-'), self.numberState)
        self.setCharacterState(ord('.'), ord('.'), self.numberState)
        self.setCharacterState(ord('"'), ord('"'), self.quoteState)
        self.setCharacterState(ord("'"), ord("'"), self.quoteState)
        self.setCharacterState(ord("/"), ord("/"), self.slashState)

        if len(args) > 0:
            s = args[0]
            self.setString(s)

    def getReader(self):
        return self.reader

    def nextToken(self):
        c = self.reader.read()
        if c != None and ord(c) < len(self.characterState):
            return self.characterState[ord(c)].nextToken(self.reader, c, self)
        return Token.EOF
    
    def setCharacterState(self, fromI, toI, state):
        for i in range(fromI, toI + 1):
            if i >= 0 and i < len(self.characterState):
                self.characterState[i] = state

    def setReader(self, r):
        self.reader = r

    def setString(self, *args):
        s = args[0]
        self.setReader(PushbackReader(s))

class TokenString:
    def __init__(self, o):
        if isinstance(o, list):
            tokens = o
            self.tokens = tokens
        else:
            if isinstance(o, str):
                s = o
                t = Tokenizer(s)
            else:
                t = o
            v = []
            while True:
                tok = t.nextToken()
                if tok.ttype == Token.TT_EOF:
                    break
                v.append(tok)
            self.tokens = copy.copy(v)

    def length(self):
        return len(self.tokens)
    
    def tokenAt(self, i):
        return self.tokens[i]
    
    def __str__(self):
        buf = ""
        for i in range(len(self.tokens)):
            if i > 0:
                buf += " "
            buf += self.tokens[i].__str__()
        return buf
    
class TokenStringSource:
    def __init__(self, *args):
        self.tokenizer = None
        self.delimiter = None
        self.cachedTokenString = None
        if len(args) == 2:
            self.tokenizer = args[0]
            self.delimiter = args[1]
    
    def ensureCacheIsLoaded(self):
        if self.cachedTokenString == None:
            self.loadCache()
    
    def hasMoreTokenStrings(self):
        self.ensureCacheIsLoaded()
        return self.cachedTokenString != None
    
    def loadCache(self):
        tokenVector = self.nextVector()
        if len(tokenVector) == 0:
            self.cachedTokenString = None
        else:
            tokens = copy.deepcopy(tokenVector)
            self.cachedTokenString = TokenString(tokens)
    
    def nextTokenString(self):
        self.ensureCacheIsLoaded()
        returnTokenString = self.cachedTokenString
        self.cachedTokenString = None
        return returnTokenString
    
    def nextVector(self):
        v = []
        while True:
            tok = self.tokenizer.nextToken()
            if tok.ttype == Token.TT_EOF or tok.sval == self.delimiter:
                break
            v.append(tok)
        return v

class Assembly:
    def __init__(self):
        self.stack = []
        self.target = None
        self.index = 0
    
    def clone(self):
        aCopy = copy.deepcopy(self)
        return aCopy
    
    def elementsConsumed(self):
        return self.index
    
    def elementsRemaining(self):
        return len(self.stack) - self.elementsConsumed()
    
    def getStack(self):
        return self.stack
    
    def getTarget(self):
        return self.target
    
    def hasMoreElements(self):
        return self.elementsConsumed() < self.length()

    def pop(self):
        return self.stack.pop()
    
    def push(self, o):
        self.stack.append(o)

    def setTarget(self, target):
        self.target = target
    
    def stackIsEmpty(self):
        return len(self.stack) == 0
    
    def __str__(self):
        delimiter = self.defaultDelimiter()
        #return str([k.value() for k in reversed(self.stack)]) + self.consumed(delimiter) + "^" + self.remainder(delimiter)
        return str([str(k) for k in reversed(self.stack)]) + self.consumed(delimiter) + "^" + self.remainder(delimiter)
    
    def unget(self, n):
        self.index -= n
        if self.index < 0:
            self.index = 0

class TokenAssembly(Assembly):
    def __init__(self, o):
        super().__init__()
        self.tokenString = None
        if isinstance(o, TokenString):
            self.tokenString = o
        else:
            self.tokenString = TokenString(o)
    
    def consumed(self, delimiter):
        buf = ""
        i = 0
        for i in range(self.elementsConsumed()):
            if i > 0:
                buf += delimiter
            buf += str(self.tokenString.tokenAt(i))
        return buf
    
    def defaultDelimiter(self):
        return "/"
    
    def length(self):
        return self.tokenString.length()
    
    def nextElement(self):
        idx = self.index
        self.index += 1
        return self.tokenString.tokenAt(idx)
    
    def peek(self):
        if self.index < self.length():
            return self.tokenString.tokenAt(self.index)
        else:
            return None
    
    def remainder(self, delimiter):
        buf = ""
        for i in range(self.elementsConsumed(), self.length()):
            if i > self.elementsConsumed():
                buf += delimiter
            buf += str(self.tokenString.tokenAt(i))
        return buf
    
class Parser:
    @classmethod
    def add(cls, v1, v2):
        for e in v2:
            v1.append(e)
                
    def __init__(self, *args):
        self.name = None
        self.assembler = None
        if len(args) == 1:
            self.name = args[0]

    def accept(self, *args):
        visiter = []
        if len(args) == 2:
            visiter = args[1]

    def best(self, v):
        _best = None
        for a in v:
            if not a.hasMoreElements():
                return a
            if _best == None:
                _best = a
            else:
                if a.elementsConsumed() > _best.elementsConsumed():
                    _best = a
        return _best
    
    def bestMatch(self, a):
        _in = []
        _in.append(a)
        out = self.matchAndAssemble(_in)
        return self.best(out)
    

    def completeMatch(self, a):
        _best = self.bestMatch(a)
        if _best != None and (not _best.hasMoreElements()):
            return _best
        return None
    
    def elementClone(self, v):
        #copy = []
        #for a in v:
        #    copy.append(a.clone())
        #return copy
        return copy.deepcopy(v)
        
    
    def getName(self):
        self.name

    #def match(self, _in):
    #    pass

    def matchAndAssemble(self, _in):
        out = self.match(_in)
        if self.assembler != None:
            for a in out:
                self.assembler.workOn(a)
        return out
    
    def randomInput(self, maxDepth, separator):
        buf = ""
        first = True
        for a in self.randomExpansion(maxDepth, 0):
            if not first:
                buf += separator
            buf += a.__str__()
            first = False
        return buf
    
    def setAssembler(self, assembler):
        self.assembler = assembler
        return self
    
    #def unvisitedString(self, visited):
    #    pass
    
    def __str__(self, *args):
        if len(args) == 0:
            visited = []
        if self.name != None:
            return self.name
        elif self in visited:
            return "..."
        else:
            visited.append(self)
            return self.unvisitedString(visited)
        
class CollectionParser(Parser):
    def __init__(self, *args):
        if len(args) == 1:
            super().__init__(args[0])
        else:
            super().__init__()
        self.subparsers = []

    
    def add(self, e):
        self.subparsers.append(e)
        return self
    
    def getSubparsers(self):
        return self.subparsers
    
    #def toStringSeparator(self):
    #    pass

    def unvisitedString(self, visited):
        buf = "<"
        needSeparator = False
        for next in self.subparsers:
            if needSeparator:
                buf += self.toStringSeparator()
            buf += str(next) # next.toString(visited)
            needSeparator = True
        buf += ">"
        return buf

import random
class Terminal(Parser):
    def __init__(self, *args):
        if len(args) == 1:
            super().__init__(args[0])
        else:
            super().__init__()
        self._discard = False

    def accept(self, *args):
        if len(args) == 2:
            pv = args[0]
            visited = args[1]
            pv.visitTerminal(self, visited)

    def discard(self):
        return self.setDiscard(True)
    
    def match(self, _in):
        out = []
        for a in _in:
            b = self.matchOneAssembly(a)
            if b != None:
                out.append(b)
        return out
    
    def matchOneAssembly(self, _in):
        if not _in.hasMoreElements():
            return None
        if self.qualifies(_in.peek()):
            out = _in.clone()
            o = out.nextElement()
            if not self._discard:
                out.push(o)
            return out
        return None

    def qualifies(self, o):
        return True
    
    def randomExpansion(self, maxDepth, depth):
        v = []
        v.append(self.__str__())
        return v
    
    def setDiscard(self, discard):
        self._discard = discard
        return self
    
    def unvisitedString(self, visited):
        return "any"
    
class Word(Terminal):
    def qualifies(self, o):
        t = o
        return t.isWord()
    
    def randomExpansion(self, maxDepth, depth):
        n = int(5 * random.random()) + 3
        letters = []
        for i in range(n):
            c = chr(int(26.0 * random.random()) + ord('a'))
            letters.append(c)
        v = "".join(letters)
        return v
    
    def unvisitedString(self, visited):
        return "Word"

class Alternation(CollectionParser):
    def __init__(self, *args):
        if len(args) == 1:
            name = args[0]
            super().__init__(name)
        else:
            super().__init__()
    
    def accept(self, *args):
        if len(args) == 2:
            pv = args[0]
            visited = args[1]
            pv.visitAlternation(self, visited)
    
    def match(self, _in):
        out = []
        for p in self.subparsers:
            Parser.add(out, p.matchAndAssemble(_in))
        return out
    
    def randomExpansion(self, maxDepth, depth):
        if depth >= maxDepth:
            return self.randomSettle(maxDepth, depth)
        n = len(self.subparsers)
        i = int(n*random.random())
        j = self.subparsers.elementAt(i)
        # なぜdepth++が必要なのか不明
        result = j.randomExpansion(maxDepth, depth)
        depth += 1
        return result
    
    def randomSettle(self, maxDepth, depth):
        terms = []
        for j in self.subparsers:
            if isinstance(j, Terminal):
                terms.append(j)
        which = terms
        if len(terms):
            which = self.subparsers
        n = len(self.subparsers)
        i = int(n*random.random())
        p = which.elementAt(i)
        # なぜdepth++が必要なのか不明
        result = p.randomExpansion(maxDepth, depth)
        depth += 1
        return result
    
    def toStringSeparator(self):
        return "|"
    
class Empty(Parser):
    def accept(self, *args):
        if len(args) == 2:
            pv = args[0]
            visited = args[1]
            pv.visitEmpty(self, visited)
    
    def match(self, _in):
        return self.elementClone(_in)
    
    def randomExpansion(self, maxDepth, depth):
        return []
    
    def unvisitedString(self, visited):
        return " empty "
    
class Repetition(Parser):
    EXPWIDTH = 4

    def __init__(self, *args):
        self.preAssembler = None
        self.subparser = args[0]
        if len(args) == 1:
            name = None
        else:
            name = args[1]
        super().__init__(name)

    def accept(self, *args):
        if len(args) == 2:
            pv = args[0]
            visited = args[1]
            pv.visitRepetition(self, visited)
    
    def getSubparser(self):
        return self.subparser
    
    def match(self, _in):
        if self.preAssembler != None:
            for a in _in:
                self.preAssembler.workOn(a)
        out = self.elementClone(_in)
        s = _in
        while len(s) > 0:
            s = self.subparser.matchAndAssemble(s)
            self.add(out, s)
        return out

    def randomExpansion(self, maxDepth, depth):
        v = []
        if depth >= maxDepth:
            return v
        n = int(Repetition.EXPWIDTH * random.random())
        for j in range(0, n):
            w = self.subparser.randomExpansion(maxDepth, depth); depth += 1
            for e in w:
                v.append(e)
        return v
    
    def setPreAssembler(self, preAssembler):
        self.preAssembler = preAssembler
        return self
    
    def unvisitedString(self, visited):
        return str(self.subparser) + "*" #self.subparser.toString(visited) + "*"
    
class Sequence(CollectionParser):
    def __init__(self, *args):
        if len(args) > 0:
            super().__init__(args[0])
        else:
            super().__init__()
    
    def accept(self, *args):
        if len(args) == 2:
            pv = args[0]
            visited = args[1]
            pv.visitSequence(self, visited)
    
    def match(self, _in):
        out = _in
        for p in self.subparsers:
            out = p.matchAndAssemble(out)
            if len(out) == 0:
                return out
        return out
    
    def randomExpansion(self, maxDepth, depth):
        v = []
        for p in self.subparsers:
            w = p.randomExpansion(maxDepth, depth); depth += 1
            for f in w:
                v.append(f)
        return v
    
    def toStringSeparator(self):
        return ""

class Literal(Terminal):
    def __init__(self, s):
        super().__init__()
        self.literal = Token(s)
    
    def qualifies(self, o):
        return self.literal == o
    
    def unvisitedString(self, visited):
        return self.literal.__str__()
    
class CaselessLiteral(Literal):
    def __init__(self, literal):
        super().__init__(literal)

    def qualifies(self, o):
        return self.literal.equalsIgnoreCase(o)
    
class QuotedString(Terminal):
    def qualifies(self, o):
        t = o
        return t.isQuotedString()
    
    def randomExpansion(self, maxDepth, depth):
        n = int(5 * random.random())
        letters = [None for i in range(n+2)]
        letters[0] = '"'
        letters[n + 1] = '"'

        for i in range(n):
            c = int(26 * random.random() + ord('a'))
            letters[i + 1] = chr(c)

        v = "".join(letters)
        return v
    
    def unvisitedString(self, visited):
        return "QuotedString"

class Symbol(Terminal):
    def __init__(self, s):
        super().__init__()
        self.symbol = Token(Token.TT_SYMBOL, s, 0)

    def qualifies(self, o):
        return self.symbol == o
    
    def unvisitedString(self, visited):
        return str(self.symbol)

import math
class Num(Terminal):
    def qualifies(self, o):
        t = o
        return t.isNumber()
    
    def randomExpansion(self, maxDepth, depth):
        d = math.floor(1000 * random.random()) / 10
        v = []
        v.append(d)
        return v
    
    def unvisitedString(self, visited):
        return "Num"

class Assembler:
    def elementsAbove(self, a, fence):
        items = []
        while not a.stackIsEmpty():
            top = a.pop()
            if top == fence:
                break
            items.append(top)
        return items
    
    def workOn(self, a):
        pass

# Logikusの文法
"""
    axiom        = structure (ruleDef | Empty);
    structure    = functor('(' commaList(term) ')' | Empty);
    functore     =  '.' | LowercaseWord | QuotedString;
    term         = structure | Num | list | variable;
    variable     = UppercaseWord | '_';
    ruleDef      = ":-" commaList(condition);
    condition    = structure | not | evaluation | comaprison | list;
    not          = "not" structure;
    evaluation   = '#' '(' arg ',' arg ')';
    comparison   = operator '(' arg ',' arg ')';
    arg          = expression | functor;
    expression   = phrase ('+' phrase | '-' phrase)*;
    phrase       = factor ('*' factor | '/' factor)*;
    list         = '[' (listContents | Empty) ']';
    listContents = commaList(term) listTail;
    listTail     = ('|' (variable | list)) | Empty;
    commaList(p) = p (',' p)*;
"""

from engine import *

class AtomAssembler(Assembler):
    def workOn(self, a):
        t = a.pop()
        if t.isQuotedString():
            s = t.sval
            plain = s[1:-1]
            a.push(Atom(plain))
        else:
            if t.isNumber():
                a.push(Atom(t.nval))
            else:
                a.push(Atom(t.value()))

class AxiomAssembler(Assembler):
    def workOn(self, a):
        s = a.getStack()
        sa = []
        for e in s:
            sa.append(e)
        a.push(Rule(sa))

class ComparisonAssembler(Assembler):
    def workOn(self, a):
        second = a.pop()
        first = a.pop()
        t = a.pop()
        a.push(Comparison(t.sval, first, second))

class EvaluationAssembler(Assembler):
    def workOn(self, a):
        second = a.pop()
        first = a.pop()
        a.push(Evaluation(first, second))

class ListAssembler(Assembler):
    def workOn(self, a):
        fence = Token('[')
        termVector = self.elementsAbove(a, fence)
        termArray = list(reversed(termVector))
        if len(termArray) == 0:
            a.push(EmptyList())
        else:
            a.push(Structure.list(termArray))

class ListWithTailAssembler(Assembler):
    def workOn(self, a):
        tail = a.pop()
        fence = Token('[')
        termVector = self.elementsAbove(a, fence)
        termArray = list(reversed(termVector))
        a.push(Structure.list(termArray, tail))

class NotAssembler(Assembler):
    def workOn(self, a):
        s = a.pop()
        a.push(Not(s))

class StructureWithTermsAssembler(Assembler):
    @classmethod
    def vectorReversedIntoTerms(cls, v):
        terms = list(reversed(v))
        return terms
    
    def workOn(self, a):
        fence = Token('(')
        termVector = self.elementsAbove(a, fence)
        termArray = list(reversed(termVector))
        t = a.pop()
        a.push(Structure(t.value(), termArray))

class VariableAssembler(Assembler):
    def workOn(self, a):
        t = a.pop()
        name = t.sval
        a.push(Variable(name))

class ArithmeticAssembler(Assembler):
    def __init__(self, operator):
        self.operator = operator
    
    def workOn(self, a):
        operand1 = a.pop()
        operand0 = a.pop()
        a.push(ArithmeticOperator(self.operator, operand0, operand1))
    
class AnonymousAssembler(Assembler):
    def workOn(self, a):
        a.push(Anonymous())

import traceback

class Track(Sequence):
    def __init__(self, *args):
        if len(args) == 0:
            super().__init__()
        else:
            name = args[0]
            super().__init__(name)
    
    def match(self, _in):
        inTrack = False
        last = _in
        out = _in
        for p in self.subparsers:
            out = p.matchAndAssemble(last)
            if len(out) == 0:
                if inTrack:
                    self.throwTrackException(last, p)
                return out
            inTrack = True
            last = out
        return out
    
    def throwTrackException(self, previousState, p):
        best = self.best(previousState)
        after = best.consumed(" ")
        if after == "":
            after = "-nothing-"
        expected = str(p)
        next = best.peek()
        found = "-nothing-" if next == None else str(next)
        raise Exception(f"After: {after}\nExpected: {expected}\nFound: {found}")

class LowercaseWord(Word):
    def qualifies(self, o):
        t = o
        if not t.isWord():
            return False
        word = t.sval
        return len(word) > 0 and word[0].islower()

    def randomExpansion(self, maxDepth, depth):
        n = int(5 * random.random()) + 3
        letters = ""
        for i in range(n):
            c = chr(int(26 * random.random()) + ord('a'))
            letters += str(c)
        return 
    
    def unvisitedString(self, visited):
        return "word"
    
class UppercaseWord(Word):
    def qualifies(self, o):
        t = o
        if not t.isWord():
            return False
        word = t.sval
        return len(word) > 0 and word[0].isupper()

    def randomExpansion(self, maxDepth, depth):
        n = int(5 * random.random()) + 3
        letters = ""
        for i in range(n):
            c = chr(int(26 * random.random()) + ord('A'))
            letters += str(c)
        return 
    
    def unvisitedString(self, visited):
        return "Word"

class LogikusParser:
    def __init__(self):
        self._structure = None
        self._expression = None
        self._list = None
    
    def arg(self):
        a = Alternation()
        a.add(self.expression())
        a.add(self.functor().setAssembler(AtomAssembler()))
        return a
    
    def axiom(self):
        s = Sequence("axiom")
        s.add(self.structure())

        a = Alternation()
        a.add(self.ruleDef())
        a.add(Empty())
        s.add(a)

        s.setAssembler(AxiomAssembler())
        return s
    
    def commaList(self, p):
        commaP = Track()
        commaP.add(Symbol(',').discard())
        commaP.add(p)

        s = Sequence()
        s.add(p)
        s.add(Repetition(commaP))
        return s
    
    def comparison(self):
        t = Track("comparison")
        t.add(self.operator())
        t.add(Symbol('(').discard())
        t.add(self.arg())
        t.add(Symbol(',').discard())
        t.add(self.arg())
        t.add(Symbol(')').discard())
        t.setAssembler(ComparisonAssembler())
        return t

    def condition(self):
        a = Alternation("condition")
        a.add(self.structure())
        a.add(self._not())
        a.add(self.evaluation())
        a.add(self.comparison())
        a.add(self.list())
        return a
    
    def divideFactor(self):
        s = Sequence("divideFactor")
        s.add(Symbol('/').discard())
        s.add(self.factor())
        s.setAssembler(ArithmeticAssembler('/'))
        return s
    
    def evaluation(self):
        t = Track("evaluation")
        t.add(Symbol('#').discard())
        t.add(Symbol('(').discard())
        t.add(self.arg())
        t.add(Symbol(',').discard())
        t.add(self.arg())
        t.add(Symbol(')').discard())
        t.setAssembler(EvaluationAssembler())
        return t
    
    def expression(self):
        if self._expression == None:
            self._expression = Sequence("expression")
            self._expression.add(self.phrase())
            a = Alternation()
            a.add(self.plusPhrase())
            a.add(self.minusPhrase())
            self._expression.add(Repetition(a))
        return self._expression
    
    def factor(self):
        a = Alternation("factor")
        s = Sequence()
        s.add(Symbol('(').discard())
        s.add(self.expression())
        s.add(Symbol(')').discard())
        a.add(s)
        a.add(self.num())
        a.add(self.variable())
        return a
    
    def functor(self):
        a = Alternation("functor")
        a.add(Symbol('.'))
        a.add(LowercaseWord())
        a.add(QuotedString())
        return a
    
    def list(self):
        if self._list == None:
            self._list = Track("list")
            self._list.add(Symbol('[')) # push this, as a fence
            a = Alternation()
            a.add(self.listContents()) 
            a.add(Empty().setAssembler(ListAssembler()))
            self._list.add(a)
            self._list.add(Symbol(']').discard())
        return self._list
    
    def listContents(self):
        s = self.commaList(self.term())
        s.add(self.listTail())
        return s
    
    def listTail(self):
        tail = Alternation()
        tail.add(self.variable())
        tail.add(self.list())

        barTail = Track("bar tail")
        barTail.add(Symbol('|').discard())
        barTail.add(tail)
        barTail.setAssembler(ListWithTailAssembler())
        
        a = Alternation()
        a.add(barTail)
        a.add(Empty().setAssembler(ListAssembler()))
        return a
    
    def minusPhrase(self):
        s = Sequence("minusPhrase")
        s.add(Symbol('-').discard())
        s.add(self.phrase())
        s.setAssembler(ArithmeticAssembler('-'))
        return s
    
    def _not(self):
        t = Track("not")
        t.add(Literal("not").discard())
        t.add(self.structure())
        t.setAssembler(NotAssembler())
        return t
    
    def num(self):
        n = Num()
        n.setAssembler(AtomAssembler())
        return n
    
    def operator(self):
        a = Alternation("operator")
        a.add(Symbol('<'))
        a.add(Symbol('>'))
        a.add(Symbol('='))
        a.add(Symbol("<="))
        a.add(Symbol(">="))
        a.add(Symbol("!="))
        return a
    
    def phrase(self):
        _phrase = Sequence("phrase")
        _phrase.add(self.factor())
        a = Alternation()
        a.add(self.timesFactor())
        a.add(self.divideFactor())
        _phrase.add(Repetition(a))
        return _phrase
    
    def plusPhrase(self):
        s = Sequence("plusPhrase")
        s.add(Symbol('+').discard())
        s.add(self.phrase())
        s.setAssembler(ArithmeticAssembler('+'))
        return s
    
    @classmethod
    def query(cls):
        p = cls.commaList(cls, cls().condition())
        p.setAssembler(AxiomAssembler())
        return p
    
    def ruleDef(self):
        t = Track("rule definition")
        t.add(Symbol(":-").discard())
        t.add(self.commaList(self.condition()))
        return t
    
    @classmethod
    def start(cls):
        return cls.axiom(cls)
    
    def structure(self):
        if self._structure == None:
            self._structure = Sequence("structure")
            self._structure.add(self.functor())

            t = Track("list in parens")
            t.add(Symbol('(')) # push this as a fence
            t.add(self.commaList(self.term()))
            t.add(Symbol(')').discard())

            a = Alternation()
            a.add(t.setAssembler(StructureWithTermsAssembler()))
            a.add(Empty().setAssembler(AtomAssembler()))
            self._structure.add(a)
        return self._structure
    
    def term(self):
        a = Alternation("term")
        a.add(self.structure())
        a.add(self.num())
        a.add(self.list())
        a.add(self.variable())
        return a
    
    def timesFactor(self):
        s = Sequence("timesFactor")
        s.add(Symbol('*').discard())
        s.add(self.factor())
        s.setAssembler(ArithmeticAssembler('*'))
        return s
    
    def variable(self):
        v = UppercaseWord()
        v.setAssembler(VariableAssembler())

        anon = Symbol('_').discard()
        anon.setAssembler(AnonymousAssembler())
        
        a = Alternation()
        a.add(v)
        a.add(anon)
        return a

class LogikusFacade:
    @classmethod
    def axiom(cls, arg):
        if isinstance(arg, TokenString):
            ts = arg
        else:
            s = arg
            ts = TokenString(s)
        p = LogikusParser().axiom()
        o = cls.parse(ts, p, "axiom")
        return o
    
    @classmethod
    def parse(cls, ts, p, _type):
        ta = TokenAssembly(ts)
        out = p.bestMatch(ta)
        if out == None:
            print("reportError")
        if out.hasMoreElements():
            if not out.remainder("") == ";":
                print("reportLeftovers")
        return out.pop()
    
    @classmethod
    def program(cls, s):
        p = Program()
        tss = TokenStringSource(Tokenizer(s), ";")
        while True:
            ts = tss.nextTokenString()
            if ts == None:
                break
            p.addAxiom(cls.axiom(ts))
        return p
    
    @classmethod
    def query(cls, s, _as):
        o = cls.parse(s, LogikusParser.query(), "query")
        if isinstance(o, Fact):
            f = o
            q = Query(_as, f)
        else:
            q = Query(_as, o)
        found = "No"
        if Program.debug:
            print(f"{q}?")
        while q.canFindNextProof():
            print(q.variables())
            found = "Yes"
        print(found)
