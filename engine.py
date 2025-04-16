# This is a port to Python of the inference engine in Steven 
# J. Metsker's book "Building Parsers with Java."
# by Hiroshi TAKEMOTO.
#
# Original Java code Copyright as follow.
#
# Copyright (c) 1999 Steven J. Metsker. All Rights Reserved.
# Steve Metsker makes no representations or warranties about
# the fitness of this software for any particular purpose, 
# including the implied warranty of merchantability.
import copy
from collections import defaultdict
import time

class Unification():
    """Structures and variables use unifications to keep track of the 
    variable assignments that make a proof work. The unification 
    class itself provides behavior for adding and accessing 
    variables. 
    """
    empty = None
    def __new__(cls, *args, **kargs):
        """define class instance variable emtpy.

        Returns:
            Unification: this class
        """        

        if cls.empty == None:
            cls.empty = super(Unification, cls).__new__(cls)
            cls.empty._variables = []
        return super(Unification, cls).__new__(cls)

    def __init__(self, v = None):
        """Creates an empty unification.

        Args:
            v: the variable with which the unification begins
        """
        self._variables = []
        if v != None:
            self.addVariable(v)
    
    def addVariable(self, v):
        """Adds all the variables of another unification to this one.

        Args:
            v (Variable): the variable to add to this unification
        Returns
            this unification
        """
        if not v in self._variables:
            self._variables.append(v)
        return self
    
    def append(self, u):
        """Adds all the variables of another unification to this one.

        Args:
            u (_type_): _description_

        Returns:
            _type_: _description_
        """        
        for v in u.elements():
            self.addVariable(v)
        return self

    def elements(self):
        """Return the variables in this unification.

        Returns:
            the variables in this unification.
        """        
        return self._variables
    
    def unbind(self):
        """Asks all the contained variables to unbind.
        """
        for v in self._variables:
            v.unbind()
    
    def __str__(self):
        """Returns a string representation of this unification.

        Returns:
            a string representation of this unification
        """        
        buf = str()
        for i in range(len(self._variables)):
            if i > 0:
                buf += ", "
            buf += self._variables[i].definitionString()
        return buf
    
class Variable:
    """A variable is a named term that can unify with  other terms.

    Instance variables:
        name: name of variable.
        instantiation: The instantiation of a variable may be another 
            variable, or a structure. 
        id: unique id of variable.
    """    
    def __init__(self, name):
        """Create a variable with the given name.

        Args:
            name (str): name of variable.
        """        
        self.name = name
        self.instantiation = None
        self.id = f"{name}_{str(time.time())}"

    def unify(self, s):
        """Unifies argument s.
        s: Structure
            Instantiates this variable with the supplied structure, or
            forwards the request to its instantiation if it already has 
            one.
        s: Variable
            Instantiates this variable with the supplied variable, or 
            forwards the request to its instantiation if it already has
            one.
        s: Term
            Unifies this variable with the supplied term.

        Args:
            s (Structure|Variable|Term): structure or variable or term to unify with.

        Returns:
            s: Structure
                a unification. If this variable is already
                instantiated, the unification is the result of
                unifying with the input structure. Otherwise, the
                result is a new unification containing just this
                variable, instantiated to the input structure.
            s: Variable
                the sum of the variables that bind to values to make
                the unification work; Returns null if the 
                unification fails.
            s: Term
                he sum of the variables that bind to values to make
                the unification work; Returns null if the 
                unification fails.
        """        
        structureCls = globals()['Structure']
        if isinstance(s, Variable):
            v = s
            if self is v:
                return Unification()
            elif self.instantiation != None:
                return self.instantiation.unify(v)
            elif v.instantiation != None:
                return v.instantiation.unify(self)
            self.instantiation = v
            return Unification(self)
        elif isinstance(s, structureCls):
            if self.instantiation != None:
                return self.instantiation.unify(s)
            self.instantiation = s
            return Unification(self)
        else: # Term
            t = s
            return t.unify(self)
        
    def __eq__(self, o):
        """Returns true if the supplied object is an equivalent 
        variable.

        Args:
            o (Object): the object to compare

        Returns:
            boolean: true, if the supplied object has the same
                name, and it the two variables' instantiations
                are equal
        """        
        if not isinstance(o, Variable):
            return False
        v = o
        if self.name != v.name:
            return False
        if self.instantiation == None:
            return v.instantiation == None
        return self.instantiation.__eq__(v.instantiation)
    
    def __hash__(self):
        """Retern a hash id.

        Returns:
            str: unique hash id.
        """        
        return hash(self.id)
    
    def unbind(self):
        """Marks this variable as no longer having an instantiated 
        value.
        """        
        self.instantiation = None


    # Implementation for Interface Term.
    def eval(self):
        """Returns the value of this variable.

        Raises:
            Exception: if this variable's value is undefined

        Returns:
            Object: the value of this variable
        """        
        if self.instantiation == None:
            raise Exception("Variable" + self.name + " is undefined")
        return self.instantiation.eval()
    
    def isList(self):
        """Returns true if this variable is uninstantiated, or if it
        contains a list.

        Returns:
            boolean: true if this variable is uninstantiated, or if
                it contains a list.
        """        
        if self.instantiation != None:
            return self.instantiation.isList()
        return True

    def listTailString(self):
        """Returns a string representation of this variable as the 
        tail of a list.

        Returns:
            str: a string representation of this variable as the 
                tail of a list
        """        
        if self.instantiation != None:
            return self.instantiation.listTailString()
        return f"|{self.name}"
        
    def __str__(self):
        """Returns a string representation of this variable.

        Returns:
            str: a string representation of this variable
        """        
        if self.instantiation != None:
            return self.instantiation.__str__()
        return self.name

    def variables(self):
        """Returns a unification containing just this variable.

        Returns:
            Unification: a unification containing just this variable
        """        
        return Unification(self)
    
    def copyForProof(self, ignored, scope):
        """Returns a copy of the term for use in a proof.

        Args:
            ignored (AxiomSource): ignored argument
            scope (Scope): variables for the provable rule copy

        Returns:
            Term: a provable copy of this Term, that will use the 
                supplied axiom source and scope
        """        
        return scope.lookup(self.name)
    
    def definitionString(self):
        """Returns string representation of this variable, showing 
        both its name and its value.

        Returns:
            str: a string representation of this variable, showing 
                both its name and its value.
        """         
        if self.instantiation != None:
            return str(self.name) + " = " + str(self.instantiation)
        return self.name

class Structure:
    """A Structure is a functor associated with a number of terms; 
    a functor can be any object. A term is an object that 
    implements the Term interface, including structures and 
    variables. 

    To be able to prove itself against a program, a structure 
    must appear in a Rule. Rules associate like-named variables 
    in a "scope", which is essentially a dictionary. A rule 
    makes an executable copy of itself by creating a new 
    variable dictionary, and by making "consulting" copies of 
    its structures.
    """
    @classmethod
    def headAndTail(cls, terms, tail):
        """This method helps the static list factories.
        A list is a structure whose functor is "." and that has two 
        terms. The first term of a list can be any term; the second 
        term of a list is another list, an empty list, or a 
        variable.

        Args:
            terms (Term[]): a list can be any term
            tail (Term): a term of a list is another list

        Returns:
            Term[]: a concatenation of the remainder of the 
                given array with the supplied tail. 
        """        
        if len(terms) == 0:
            raise Exception("Cannot create a list with no head")
        headAndTail = []
        headAndTail.append(terms[0]) 
        if len(terms) == 1:
            headAndTail.append(tail) 
        else:
            rest = copy.copy(terms[1:])
            headAndTail.append(cls.list(rest, tail)) 
        return headAndTail

    @classmethod
    def list(cls, *args):
        """Constructs a list.

        args: Object[] 
            a list that contains the supplied object, wrapped as Facts.

        args: Term[]
            a list of two terms, regardless of 
            the number of terms supplied here. The new list's first 
            term is the first term of the supplied array. Its second 
            term is a list of the remaining terms.
        args: Term[] terms, Term tail:
            terms: the leading terms of the list. In practice, 
                this array usually contains a single term.
            tail: a list, or a variable that represents the tail 
                of the list.
        Returns:
            Object[]: the contents of the list
        """        
        factCls = globals()['Fact']
        if len(args) == 1:
            if isinstance(args[0], list):
                terms = args[0]
                emptyListCls = globals()['EmptyList']
                if isinstance(terms[0], Structure) or isinstance(terms[0], Variable):
                    return Structure(".", cls.headAndTail(terms, emptyListCls()))
                else:
                    return Structure(".", cls.headAndTail(factCls.facts(terms), emptyListCls()))
        elif len(args) == 2:
            terms = args[0]
            tail = args[1]
            return Structure(".", cls.headAndTail(terms, tail))
        
    def isList(self):
        """Return true, if this structure is a list, which means it
        has an functor of ".", and has two terms, the second of which
        must be a list.

        Returns:
            boolean: true   if this structure is a list
        """        
        return len(self.terms) == 2 and self.functor == "." and self.terms[1].isList()
    
    def listTailString(self):
        """Returns a representation of this list as the inner part of 
        some other list.

        Returns:
            str: a representation of this list.
        """        
        return f", {self.listTermsToString()}"
    
    def listTermsToString(self):
        """Return a textual represenation of this list's terms, with 
        a normal representation of the first term, and with the
        second term as the tail of a list.

        Returns:
            str: a textual represenation of this list's terms
        """        
        s = self.terms[0].__str__()
        if len(self.terms) > 1:
            s += self.terms[1].listTailString()
        return s
    
    # コンストラクター
    def __init__(self, functor, terms = []):
        """Contructs a structure.

        Args:
            functor (Object): the functor for this structure
            terms (list, optional): the terms of the structure, which may be 
                either variables or other structures
        """        
        self.functor = functor
        self.terms = terms
        if terms != None and len(terms) > 0:
            self.terms = terms
    
    def arity(self):
        """Return the number of terms in this structure.

        Returns:
            int: the number of terms in this structure
        """        
        return len(self.terms)
    
    def canFindNextProof(self):
        """Returns False.

        Returns:
            boolean: False
        """        
        return False
    
    def copyForProof(self, _as, scope):
        """Create a <code>ConsultingStructure</code> counterpart that
        can unify with other structures.

        Args:
            _as (AxiomSource): where to find axioms to prove against
            scope (Scope): the scope to use for variables in the ConsultingStructure

        Returns:
            Term: a ConsultingStructure counterpart that
                can unify with other structures.
        """        
        newTerms = []
        for t in self.terms:
            newTerms.append(t.copyForProof(_as, scope))
        # ConsultingStructureを直接使えないので、クラス名からインスタンスを生成
        cls = globals()['ConsultingStructure']
        return cls(_as, self.functor, newTerms)
    
    def __eq__(self, o):
        """Returns true if the supplied object is an equivalent 
        structure.

        Args:
            o (Object): the object to compare

        Returns:
            boolean: true, if the supplied object's functor equals
                this structure's functor, and both structures'
                terms are all equal.
        """        
        if type(self) != type(o):
            return False
        s = o
        if not self.functorAndArityEquals(s):
            return False
        for i in range(self.arity()):
            if not self.terms[i].__eq__(s.terms[i]):
                return False
        return True
    
    def functorAndArityEquals(self, s):
        """Returns True if this structure's functor and 
        number of terms match the supplied structure.

        Args:
            s (Structure): the structure to compare this one against

        Returns:
            boolean: True if this structure's functor and 
                number of terms match the supplied structure
        """        
        return self.arity() == s.arity() and self.functor.__eq__(s.functor)
    
    def unify(self, s):
        if isinstance(s, Structure):
            if not self.functorAndArityEquals(s):
                return None
            u = Unification()
            others = s.terms
            for i in range(len(self.terms)):
                subUnification = self.terms[i].unify(others[i])            
                if subUnification == None:
                    u.unbind()
                    return None
                u.append(subUnification)
            return u
        elif isinstance(s, Variable):
            v = s
            return v.unify(self)
        else: # Term
            t = s
            return t.unify(self)
    
    def eval(self):
        """Return this structure, if it is nonatomic, or just the
        functor, if this is an atom.

        Returns:
            Object: this structure
        """        
        if len(self.terms) > 0:
            return self
        return self.functor
    
    def __str__(self):
        """Returns a string representation of this structure. 

        Returns:
            str: a string representation of this structure
        """        
        if self.isList():
            return f"[{self.listTermsToString()}]"
        buf = str(self.functor)
        if self.terms != None and len(self.terms) > 0:
            buf += "("
            for i in range(len(self.terms)):
                if i > 0:
                    buf += ", "
                buf += self.terms[i].__str__()
            buf += ")"
        return buf
    
    def variables(self):
        """Returns the variables of the terms of this structure.

        Returns:
            Unification: unification all the variables of the terms of this 
                structure
        """        
        u = Unification()
        if len(self.terms) > 0:
            for t in self.terms:
                u.append(t.variables())
        return u

class Scope:
    """A scope is a repository for variables. A dynamic rule has
    a scope, which means that variables with the same name
    are the same variable.
    """    
    def __init__(self, terms=[]):
        """Create a scope that uses the variables in the supplied
        terms.

        Args:
            terms (list, optional): the terms to seed this scope with. Defaults to [].
        """        
        self.dictionary = {}
        for t in terms:
            u = t.variables()
            for v in u.elements():
                self.dictionary[v.name] = v
    
    def clear(self):
        """Remove all variables from this scope.
        """        
        self.dictionary.clear()

    def lookup(self, name):
        """Returns a variable of the given name from this scope.
        If the so-named variable is not already in this scope,
        the scope will create it and add the variable to itself.

        Args:
            name (str): the variable name

        Returns:
            Variable: a variable of the given name from this scope
        """        
        v = self.dictionary.get(name)
        if v == None:
            v = Variable(name)
            self.dictionary[name] = v
        return v

class Rule:
    """A Rule represents a logic statement that a structure is true 
    if a following series of other structures are true. 
    """    
    def __init__(self, structures=[]):
        """Construct rule from the given structures.

        Args:
            structures (list, optional): the structures that make up this rule. Defaults to [].
        """        
        self.structures = structures

    def dynamicAxiom(self, axiomSource):
        """Return a provable version of this rule.

        Args:
            axiomSource (AxiomSource): the axiom source

        Returns:
            DynamicAxiom: a provable version of this rule
        """        
        return DynamicRule(axiomSource, Scope(), self)
    
    def head(self):
        """Return the first structure in this rule.

        Returns:
            Structure: the first structure in this rule
        """        
        return self.structures[0]
    
    def __eq__(self, o):
        """Returns true if the supplied object is an equivalent 
        rule.

        Args:
            o (Object): the object to compare

        Returns:
            boolean: true, if the supplied object's structures equal
                this rule's structures
        """        
        if not isinstance(o, Rule):
            return False
        r = o
        if len(self.structures) != len(r.structures):
            return False
        for i in range(self.structures):
            if self.structures[i] != r.structures[i]:
                return False
        return True
    
    def __str__(self):
        """Returns a string representation of this rule. 

        Returns:
            str: a string representation of this rule.
        """        
        buf = str("")
        for i in range(len(self.structures)):
            if i == 1:
                buf += " :- "
            if i > 1:
                buf += ", "
            buf += self.structures[i].__str__()
        return buf

class ConsultingStructure(Structure):
    """A ConsultingStructure is structure that can prove itself 
    against an axiom source supplied with the constructor.
    """    
    def __init__(self, source, functor, terms=[]):
        """Constructs a consulting structure with the specified functor 
        and terms, to consult against the supplied axiom source.
        This constructor is for use by Structure. 

        Args:
            source (AxiomSource): axiom source
            functor (Object): functor
            terms (list, optional): structure terms. Defaults to [].
        """        
        super().__init__(functor, terms)
        self.source = source
        self._axioms = None
        self.currentUnification = None
        self.resolvent = None
    
    def axioms(self):
        """Returns the axioms that a consulting structure can
        consult. Note that after canUnify fails, this object will
        set its axioms to null, which forces its proving
        attempts to start over at the beginning of the source.

        Returns:
            Axiom[]: the axioms that a consulting structure can
                consult
        """        
        if self._axioms == None:
            self._axioms = iter(self.source.axioms(self))
        return self._axioms
    
    def canFindNextProof(self):
        """Tests if this structure can find another proof, and, if so, 
        sets this structure's variables to the values that make the 
        proof true.

        Returns:
            boolean: True if this structure can find another 
                proof.
        """

        # A consulting structure proves itself by unifying with rule 
        # in a program. When that rule has more than one structure, 
        ## the proving structure takes the tail of the rule as its 
        # "resolvent". The resolvent is the remainder of the rule, 
        # which, if proven true, confirms the truth of this 
        # structure. The resolvent may have multiple different 
        # proofs, and each of these counts as a new proof of this 
        # structure.       
        if self.resolvent != None:
            if self.resolvent.canFindNextProof():
                return True
        while True:
            # Find a new axiom to prove.            
            self.unbind()
            # Show that the unifying axiom's remainder is either
            # empty or provable.
            if not self.canUnify():
                self._axioms = None
                return False
            if self.resolvent.canEstablish():
                if Program.debug:
                    print(f"\tReturn: {self.variables()}")
                return True
    
    def canUnify(self):
        """Return true if this structure can unify with another rule in the 
        program.

        Returns:
            boolean: True if this structure can unify with 
                an axiom in the axiom source
        """        
        while (a := next(self.axioms(), None)):
            h = a.head()
            if not self.functorAndArityEquals(h):
                continue
            aCopy = a.dynamicAxiom(self.source)
            if Program.debug:
                print(f"\t{h}", end="")
            self.currentUnification = aCopy.head().unify(self)
            self.resolvent = None
            if self.currentUnification != None:
                self.resolvent = aCopy.resolvent()
                # デバッグトレース
                if Program.debug:
                    if not self.resolvent.isEmpty():
                        print(f"\tTrue\t{self.currentUnification} => {self.resolvent}")
                    else:
                        print(f"\tTrue\t{self.currentUnification}")
                return True
            elif Program.debug:
                print(f"\tFalse")
        return False
    
    def unbind(self):
        """Release the variable bindings that the last unification 
        produced.
        """
        if self.currentUnification != None:
            self.currentUnification.unbind()
        self.currentUnification = None
        self.resolvent = None


class DynamicRule(Rule):
    """A DynamicRule represents a provable statement that a 
    structure is true if a following series of other 
    structures are true.
    """    
    def __init__(self, _as, scope, arg):
        """Construct a provable rule for the given axiom source.

        Args:
            _as (AxiomSource): the source to consult for proving
                the structures in this dynamic rule
            scope (Scope): a home for the variables in this dynamic
                rule
            arg (Rule): the non-dynamic source of this rule.
            arg (Structure[]): structures
        """        
        if isinstance(arg, Rule):
            rule = arg
            structures = self.provableStructures(_as, scope, rule.structures)
        else:
            structures = arg
        super().__init__(structures)
        self._as = _as
        self.scope = scope
        self._tail = None
        self.headInvolved = False

    def canEstablish(self):
        """"Can establish" means that either a rule can prove itself, or
        that the rule is empty. 

        When a structure unifies with the head of a rule, the 
        structure asks the rule's tail if it can "establish" itself.
        This amounts to proving the tail, unless this rule is
        empty. If this rule is empty, it can "establish" itself,
        but it cannot "find next proof".

        Returns:
            boolean: True if this rule is empty, or
                if it is nonempty and can find another proof
        """        
        if self.isEmpty():
            return True
        return self.canFindNextProof()
    
    def canFindNextProof(self):
        """Tests if this rule can find another proof, and, if so, sets 
        this rule's variables to the values that make the proof true.

        Returns:
            boolean: True if this rule can find another 
                proof.
        """        
        if self.isEmpty():
            return False
        # If we have already found a proof, the next proof may 
        # come by finding another proof of the tail.
        if self.headInvolved:
            if self.tail().canFindNextProof():
                return True
        # Prove our structures or give up. If the head is provable,
        # it means the head has unified with another rule in the 
        # program. Our task then is to establish that either the 
        # tail is empty, or that it is provable. "Can establish" 
        # means is empty or provable.
        while True:
            self.headInvolved = self.head().canFindNextProof()
            if not self.headInvolved:
                return False
            if self.tail().canEstablish():
                return True

    def isEmpty(self):
        """Return true if this rule contains no 
        structures.

        Returns:
            boolean: True if this rule contains no structures.
        """        
        return len(self.structures) == 0
    

    def provableStructures(self, _as, scope, structures):
        """Create provable versions of an input array of structures.

        Args:
            _as (AxiomSource): the source to consult for proving
                the structures in this dynamic rule
            scope (Scope): a home for the variables in this dynamic
                rule
            structures (Structure[]): structures

        Returns:
            Structure[]: provable versions of an input array of structures.
        """        
        provables = []
        for s in structures:
            if isinstance(s, Fact):
                provables.append(ConsultingStructure(_as, s.functor, s.terms))
            else:
                provables.append(s.copyForProof(_as, scope))
        return provables

    def resolvent(self):
        """Returns the series of structures which, if proven, prove
        the truth of the head.

        Returns:
            DynamicRule: the tail of this rule
        """        
        return self.tail()
    
    def tail(self):
        """Returns the series of structures after the head.

        Returns:
            DynamicRule: the tail of this rule
        """        
        if self._tail == None:
            rest = copy.copy(self.structures[1:])
            self._tail = DynamicRule(self._as, self.scope, rest)
        return self._tail
    
    def variables(self):
        """Returns this executable rule's variables.

        Returns:
            Unification: unification  a collection of variables from this
                rule
        """        
        if len(self.structures) == 0:
            return Unification.empty
        return self.head().variables().append(self.tail().variables())
    

class Fact(Structure):
    """A Fact is a Structure that contains only other Facts.    
    """    
    _resolvent = DynamicRule(None, None, [])

    @classmethod
    def facts(cls, objects):
        """Create an array of (atomic) facts from an array of
        objects.

        Args:
            objects (Object[]): an array of facts

        Returns:
            Fact[] : an array of Atoms
        """        
        terms = []
        for o in objects:
            terms.append(Atom(o))
        return terms
    
    def __init__(self, functor, *args):
        """Contructs a fact from the specified object.

        Args:
            args = functor (Object): 
                functor: the functor for this fact
            args = (functor, objects)
                functor: the functor for this fact
                objects: the objects to convert into atoms
                    and use as the terms of this fact
            args = (functor, terms)
                functor: the functor for this fact
                terms: the terms of this fact, which can only
                    be other facts
        """        
        if len(args) == 0:
            super().__init__(functor)
        elif len(args) == 1:            
            if isinstance(args[0], list):
                first = args[0]
                if len(first) > 0 and isinstance(first[0], Fact):
                    super().__init__(functor, first)
                else:
                    atoms = [Atom(o) for o in first]
                    super().__init__(functor, atoms)
            elif isinstance(args[0], Fact):
                super().__init__(functor, [args[0]])
            else:
                super().__init__(functor, [Atom(args[0])])
        elif len(args) == 2:
            o1 = args[0]
            o2 = args[1]
            if isinstance(o1, Atom):
                super().__init__(functor, [o1, o2])
            else:
                super().__init__(functor, [Atom(o1), Atom(o2)])
    
    def unify(self, f):
        # 注意: fがFactでない場合、superのunifyを呼ぶ
        if not isinstance(f, Fact):
            return super().unify(f)
        if not self.functorAndArityEquals(f):
            return None
        for i in range(len(self.terms)):
            f1 = self.terms[i]
            f2 = f.terms[i]
            if f1.unify(f2) == None:
                return None
        return Unification.empty
    
    def dynamicAxiom(self, ignored):
        """Returns this fact.

        Args:
            ignored (AxiomSource): ignored

        Returns:
            Fact: this fact
        """        
        return self
    
    def resolvent(self):
        """Returns an empty resolvent

        Returns:
            DynamicRule: a dynamic rule with nothing in it
        """        
        return Fact._resolvent
    
    def head(self):
        """Returns this fact.

        Returns:
            Structure: this fact
        """        
        return self
    
    def copyForProof(self, ignored, ignored2):
        """Returns this fact.

        Args:
            ignored (AxiomSource): ignored
            ignored2 (Scope): ignored

        Returns:
            Term: this fact
        """        
        return self
    
class Atom(Fact):
    """An Atom is a Structure that no terms.
    """    
    def __init(self, functor):
        """Contructs an atom from the specified object.

        Args:
            functor (Object): the functor for this atom
        """        
        super().__init__(functor)

    def eval(self):
        """Returns the functor if this structure.

        Returns:
            Object: the functor if this structure
        """        
        return self.functor
    
    def __str__(self):
        """Returns a string representation of this atom. 

        Returns:
            str: a string representation of this atom.
        """
        if isinstance(self.functor, str) and ' ' in self.functor:
            return f'"{self.functor}"'
        else:
            return super().__str__()

class EmptyList(Fact):
    """The EmptyList is a list with no terms.
    """    
    def __init__(self):
        """Constructs the empty list singleton.
        """        
        super().__init__(".")
    
    def isList(self):
        """Return true, since an empty list is a list.

        Returns:
            boolean: True
        """        
        return True
    
    def listTailString(self):
        """Returns a string representation of this list as a part of 
        another list. When the empty list represents itself as part
        of another list, it just returns "".

        Returns:
            str: an empty string
        """        
        return ""
    
    def __str__(self):
        """Returns a string representation of the empty list.

        Returns:
            str: a string representation of the empty list
        """    
        return "[]"
    
class Program:
    """A Program is a collection of rules and facts that together
    form a logical model.
    """    
    debug = False
    def __init__(self, axioms=[]):
        """Create a new program with the given axioms.

        Args:
            axioms (list, optional): the given axioms. Defaults to [].
        """        
        self._axioms = None
        self._elements = []
        for axiom in axioms:
            self.addAxiom(axiom)
    
    def addAxiom(self, a):
        """Adds an axiom to this program.

        Args:
            a (Axiom): the axiom to add.
        """        
        self._elements.append(a)

    def append(self, _as):
        """Appends all the axioms of another source to this one.

        Args:
            _as (AxiomSource): the source of the new axioms
        """        
        e = _as.axioms()
        for a in e:
            self.addAxiom(a)
            
    def axioms(self, *args):
        """Returns an enumeration of the axioms in this program.

        Returns:
            Axiom[]: an enumeration of the axioms in this program.
        """        
        return iter(self._elements)
    
    def __str__(self):
        """Returns a string representation of this program. 

        Returns:
            str: a string representation of this program.
        """        
        buf = str()
        haveShownALine = False
        for e in self.axioms():
            if haveShownALine:
                buf += "\n"
            buf += e.__str__()
            buf += ";"
            haveShownALine = True
        return buf

class Query(DynamicRule):
    """A Query is a dynamic rule that stands outside of a program 
    and proves itself by referring to a program.
    """    
    def __init__(self, _as, *args):
        """Create a query from the given structures, to prove itself
        against the given axiom source.

        Args:
            _as (AxiomSource): _description_
            args = structures: the structures to prove
            args = Rule: he rule that contains structures to prove            
        """        
        self._tail = None
        if len(args) == 1:
            if isinstance(args[0], Rule):
                rule = args[0]
                scope = Scope(rule.structures)
                structures = rule.structures
            else:
                if isinstance(args[0], Structure):
                    structures = [args[0]]
                else:
                    structures = args[0]
                scope = Scope(structures)
        elif len(args) == 2:
            scope = args[0]
            structures = args[1]
        super().__init__(_as, scope, super().provableStructures(_as, scope, structures))
    
    def __str__(self):
        """Returns a string representation of this query. 

        Returns:
            str: a string representation of this query.
        """        
        buf = str("")
        for i in range(len(self.structures)):
            if i > 0:
                buf += ", "
            buf += self.structures[i].__str__()
        return buf
    
class Gateway(Structure):
    """A Gateway is a structure that can prove its truth at most 
    once before failing. 
    """    
    def __init__(self, functor, terms=[]):
        """Allows subclasses to use this form of constructor. This typically
        happens when the subclass object is creating an executable copy
        of itself.

        Args:
            functor (Object): the functor for this gateway
            terms (list, optional): the program the gateway will prove itself 
                against. Defaults to [].
        """        
        super().__init__(functor, terms)
        self.open = False
    
    def canFindNextProof(self):
        """Returns true if the gate is closed and this gateway can find a new 
        proof.

        A gateway is a structure that can prove itself in at most one 
        way. After a successful proof, a gateway leaves its gate open.

        If the gate is open when this method executes, this method will 
        shut the gate and return false. This occurs after a gateway has 
        proven itself true once, and a rule has failed back to the point 
        where it is asking the gateway for another proof.

        If the gate is not open, this gateway will try to prove itself. 
        Then,
        - If the gate is not open and this gateway can prove itself, then 
            this method will return true and leave the gate open. Returning 
            true allows the containing rule to go on to prove whatever 
            structures follow this one. When the rule fails back to this 
            gateway, the gate will be open, and at that time this gateway 
            will fail.
        - If the gate is not open and this gateway can not prove itself, 
            this method returns false.
        
        Upon leaving the gate closed, this method unbinds any variables 
        that instantiated as part of this gateway's proof. This method 
        also sets rule checking to begin again at the first program rule, 
        upon the next request for a proof sent to this gateway.

        Returns:
            boolean: True if the gate is closed and this gateway can find a 
                new proof
        """
        if self.open:
            self.open = False
        else:
            self.open = self.canProveOnce()
        if not self.open:
            self.cleanup()
        return self.open
    
    def canProveOnce(self):
        """Returns true if the comparison operator holds true between each 
        pair of terms.

        Returns:
            boolean: True
        """        
        return True
    
    def cleanup(self):
        """Clean up this.

        Returns:
            boolean: True
        """        
        return None

class Comparison(Gateway):
    """A Comparison object applies a comparison operator to its 
    terms in order to prove itself. 
    """    
    def __init__(self, operator, term0, term1):
        """Create a comparison with the specified operator and
        comparison terms.

        Args:
            operator (String): the comparison operator
            term0 (ComparisonTerm): the first term
            term1 (ComparisonTerm): the second term
        """        
        super().__init__(operator, [term0, term1])
        self.operator = operator
        self.term0 = term0
        self.term1 = term1
    
    def canProveOnce(self):
        """Returns true if the comparison operator holds true between 
        the values of this comparison's terms.

        Returns:
            boolean: True if the comparison operator holds true
        """        
        p0 = self.term0.eval()
        p1 = self.term1.eval()
        if not self.compare(p0, p1):
            return False
        return True
    
    def compare(self, obj0, obj1):
        """Returns the result of comparing two objects, using the 
        indicated comparison operator.

        Args:
            obj0 (Object): a string or number to compare
            obj1 (Object): a string or number to compare

        Returns:
            boolean: the result of comparing two objects
        """        
        if (isinstance(obj0, int) or isinstance(obj0, float)) and (isinstance(obj1, int) or isinstance(obj1, float)):
            return self.compareNumber(obj0, obj1)
        elif isinstance(obj0, str) and isinstance(obj1, str):
            return self.compareString(obj0, obj1)
        else:
            return False
        
    def compareNumber(self, d0, d1):
        """Returns the result of comparing two Numbers, using the 
        indicated comparison operator.

        Args:
            d0 (Number): a Number to compare
            d1 (Number): a Number to compare

        Returns:
            boolean: the result of comparing the two numbers
        """        
        if self.operator == ">":
            return d0 > d1
        elif self.operator == "<":
            return d0 < d1
        elif self.operator == "=":
            return d0 == d1
        elif self.operator == ">=":
            return d0 >= d1
        elif self.operator == "<=":
            return d0 <= d1
        elif self.operator == "!=":
            return d0 != d1
        else:
            return False
        
    def compareString(self, s0, s1):
        """Returns the result of comparing two Strings, using the 
        indicated comparison operator.

        Args:
            s0 (str): a String to compare
            s1 (str): _desca String to compareiption_

        Returns:
            boolean: the result of comparing the two strings
        """        
        if self.operator == ">":
            return s0 > s1
        elif self.operator == "<":
            return s0 < s1
        elif self.operator == "=":
            return s0 == s1
        elif self.operator == ">=":
            return s0 >= s1
        elif self.operator == "<=":
            return s0 <= s1
        elif self.operator == "!=":
            return s0 != s1
        else:
            return False

    def copyForProof(self, ignored, scope):
        """Create a copy that uses the provided scope.

        Args:
            ignored (AxiomSource): ignored
            scope (Scope): the scope to use for variables in the copy

        Returns:
            Term: a copy that uses the provided scope
        """        
        return Comparison(
            self.operator,
            self.term0.copyForProof(None, scope),
            self.term1.copyForProof(None, scope))
    
    def eval(self):
        """Returns True if the comparison
        operator holds true between the values of the two
        terms.

        Returns:
            Object: True if the comparison
                operator holds true between the values of the two
                terms. 
        """        
        return self.canProveOnce()

class ArithmeticOperator(Structure):
    """An ArithmeticOperator represents an arithmetic operation 
    that will perform itself as part of a proof. 
    """    
    def __init__(self, operator, term0, term1):
        """Constructs an arithmetic operator with the indicated operator and 
        terms.

        Args:
            operator (str): the operator
            term0 (ArithmeticTerm): the first term
            term1 (ArithmeticTerm): the second term
        """        
        super().__init__(operator, [term0, term1])
        self.operator = operator
        self.term0 = term0
        self.term1 = term1
    
    def arithmeticValue(self, d0, d1):
        """Do the math.

        Args:
            d0 (float): the first value
            d1 (float): the second value

        Returns:
            float: a result of operation.
        """        
        result = 0
        if self.operator == "+":
            result = d0 + d1
        elif self.operator == "-":
            result = d0 - d1
        elif self.operator == "*":
            result = d0 * d1
        elif self.operator == "/":
            result = d0 / d1
        elif self.operator == "%":
            result = d0 // d1
        else:
            result = 0.0
        return result

    def copyForProof(self, ignored, scope):
        """Create a copy using the supplied scope for variables.

        Args:
            ignored (AxiomSource): ignored
            scope (Scope): the scope to use for variables 

        Returns:
            Term: a copy with variables from the supplied scope
        """        
        return ArithmeticOperator(
            self.operator,
            self.term0.copyForProof(None, scope),
            self.term1.copyForProof(None, scope))
    
    def eval(self, *args):
        """Returns the result of applying this object's operator 
        against the  arithmetic values of its two terms.

        Raises:
            Exception: if either term is not a valid arithmetic value

        Returns:
            Object: the result of applying this object's operator to 
                the arithmetic value of its two terms
        """        
        if len(args) == 0:
            d0 = self.eval(self.term0)
            d1 = self.eval(self.term1)
            return self.arithmeticValue(d0, d1)
        elif len(args) == 1:
            t = args[0]
            o = t.eval()
            if o == None:
                raise Exception(f"{t} is undefined in {self}")
            return o

# My custom gateway for write args.
class Write(Gateway):
    def __init__(self, *args):
        newArgs = []
        for a in list(args):
            if isinstance(a, str) or isinstance(a, int) or isinstance(a, float):
                a = Atom(a)
            newArgs.append(a)
        super().__init__("write", newArgs)
        self.terms = newArgs
        self.currentUnification = None
    
    def canProveOnce(self):
        """Write args.

        Returns:
            boolean: True if write successfuly.
        """        
        try:
            for t in self.terms:
                print(t.eval(), end="")
            print("")
        except:
            print("undefined")
            return False
        return True
        
    def copyForProof(self, ignored, scope):
        """Create a copy using the supplied scope for variables.

        Args:
            ignored (AxiomSource): ignored
            scope (Scope): the scope to use for variables 

        Returns:
            Term: a copy with variables from the supplied scope
        """        
        newTerm = []
        for t in self.terms:
            newTerm.append(t.copyForProof(None, scope))
        return Write(*newTerm)
    
    def eval(self):
        """Return result of write.

        Returns:
            boolean: True if write successfully
        """        
        return self.canProveOnce()
    
class Evaluation(Gateway):
    """An Evaluation unifies a term with the value of 
    another term.
    """    
    def __init__(self, term0, term1):
        """Constructs an Evaluation that will unify the first term 
        with the second term during proofs.

        Args:
            term0 (Term): the first term to unify
            term1 (Term): the term whose value should unify 
                with the first term
        """        
        super().__init__("#", [term0, term1])
        self.term0 = term0
        self.term1 = term1
        self.currentUnification = None
    
    def canProveOnce(self):
        """Returns true if this Evaluation can unify its first term 
        with the value of its second term.

        Returns:
            boolean: True, if this Evaluation can unify 
                its first term with the arithmetic value of its 
                second term
        """        
        try:
            o = self.term1.eval()
        except:
            return False
        self.currentUnification = self.term0.unify(Atom(o))
        return self.currentUnification != None
    
    def cleanup(self):
        """The superclass calls this after the evaluation has
        succeeded once, and rule is now failing backwards. The
        assigment needs to undo any binding it did on the way
        forward.
        """
        self.unbind()

    def copyForProof(self, ignoed, scope):
        """Create a copy that uses the provided scope.

        Args:
            ignoed (AxiomSource): ignored
            scope (Scope): the scope to use for variables in the
            copy

        Returns:
            Term: a copy that uses the provided scope
        """        
        return Evaluation(
            self.term0.copyForProof(None, scope),
            self.term1.copyForProof(None, scope)
        )
    
    def unbind(self):
        """Releases the variable bindings that the last unification produced.
        """        
        if self.currentUnification != None:
            self.currentUnification.unbind()
        self.currentUnification = None

class ConsultingNot(Gateway):
    """A ConsultingNot is a Not that has an axiom source to
    consult.
    """    
    def __init__(self, consultingStructure):
        """Contructs a ConsultingNot from the specified consulting
        structure. This constructor is for use by Not.

        Args:
            consultingStructure (Structure): the structure to negate
        """        
        super().__init__(consultingStructure.functor, consultingStructure.terms)
        self.consultingStructure = consultingStructure

    def canProveOnce(self):
        """Returns False if there is any way to prove this
        structure.

        Returns:
            boolean: False if there is any way to prove 
                this structure
        """        
        return not (self.consultingStructure.canUnify() and 
                    self.consultingStructure.resolvent.canEstablish())
    
    def cleanup(self):
        """After succeeding once, unbind any variables bound during
        the successful proof, and set the axioms to begin
        again at the beginning.
        """
        self.consultingStructure.unbind()
        self.consultingStructure._axioms = None

    def __str__(self):
        """Returns a string description of this Not.

        Returns:
            str: a string description of this Not
        """        
        return f"not {self.consultingStructure}"
    
class Not(Structure):
    """A Not is a structure that fails if it can prove itself 
    against a program.
    """    
    def __init__(self, *args):
        """Contructs a Not from args.

        Args:
            args = functor: the functor for this structure
            args = (functor, terms):
                functor: the functor for this structure
                terms: the terms of the structure, which may be either
                    variables or other structures
            args = (structure): the structure to negate
        """        
        if len(args) == 1:
            if isinstance(args[0], str):
                functor = args[0]
                super().__init__(functor, [])
            elif isinstance(args[0], Structure):
                s = args[0]
                super().__init__(s.functor, s.terms)
        else:
            functor = args[0]
            terms = args[1]
            super().__init__(functor, terms)
    
    def copyForProof(self, _as, scope):
        """Create a ConsultingNot counterpart that
        can prove itself.mmary_

        Args:
            _as (AxiomSource): where to find axioms to prove
                against
            scope (Scope): the scope to use for variables in the
                ConsultingStructure

        Returns:
            Term: ConsultingNot counterpart that
                can prove itself
        """        
        newTerms = []
        for t in self.terms:
            newTerms.append(t.copyForProof(_as, scope))
        return ConsultingNot(ConsultingStructure(_as, self.functor, newTerms))
    
    def __eq__(self, o):
        """Returns true if the supplied object is an equivalent 
 * not structure.

        Args:
            o (Object): the object to compare

        Returns:
            boolean: true, if the supplied object is a Not, and
                the two object's sub-structures are equal
        """        
        if not isinstance(o, Not):
            return False
        n = o
        if not self.functorAndArityEquals(n):
            return False
        for i in range(len(self.terms)):
            if not self.terms[i].__eq__(n.terms[i]):
                return False
        return True
    
    def __str__(self):
        """Returns a string description of this Not.

        Returns:
            str: a string description of this Not
        """        
        return f"not {super().__str__()}"
    
class Anonymous(Variable):
    """An anonymous variable unifies successfully with any other 
    term, without binding to the term. 
    """    
    def __init__(self):
        """Constructs an anonymous variable.
        """        
        super().__init__("_")

    def copyForProof(self, ignored, ignored2):
        """Returns this anonymous variable, which does not unify
        with anything and thus does not need to copy itself.

        Args:
            ignored (AxiomSource): ignored
            ignored2 (Scope): ignored

        Returns:
            Term: this anonymous variable
        """        
        return self
    
    def eval(self):
        """Return the value of this anonymous variable to use in
        functions; this is meaningless in logic programming,
        but the method returns the name of this variable.

        Returns:
            Object: the name of the anonymous variable
        """        
        return self.name
    
    def unify(self, ignored):
        """Returns an empty unification.

        Args:
            ignored (Structure): ignored

        Returns:
            Unification: A successful, but empty, unification 
        """        
        return Unification.empty
    
    def variables(self):
        """Returns an empty unification.

        Returns:
            Unification: an empty unification
        """        
        return Unification.empty

