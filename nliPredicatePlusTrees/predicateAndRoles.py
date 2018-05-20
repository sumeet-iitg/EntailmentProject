
from enum import IntEnum
import re

class SRL_TAGS(IntEnum):
    ID = 0
    WORD = 1
    POS = 3
    DEP = 5
    UDR = 6
    FRAME = 13

class ROLE_TYPE(IntEnum):
    ROOT = 0
    SUBJ = 1
    OBJ = 2
    # Verb clause shouldn't be added as sub-property
    VB_CLS = 3
    MOD = 4
    # Conjunction shouldn't be added as sub-property
    CONJ = 5
    MARK = 6
    AUX = 7
    COMP = 8
    CD = 9
    NEG = 10
    COMP_PRT = 11
    # possesive noun
    NN_POS = 12
    # an adj clause can be added as property
    JJ_CLS = 13
    # for all amod, advmod and nmod as
    JJ_MOD = 14
    # noun modifier the actor needs to be properly resolved
    NN_MOD = 15
    # personal pronoun, modifier and possessive should be resolved
    PRP = 16
    PRP_MOD = 17
    PRP_POS = 18
    # preposition
    IN = 19


'''
Different types of prepositions
Should take two arguments - (before and after IN).
This helps determine the relationship between clauses.
'''
class In_Type(IntEnum):
    Before = 0, # before time
    After = 1, # after time
    As = While = 2, # parallel same time
    In = Into = Among = Within = Inside = 3, #subsume relation
    Across = Behind = Outside = Out = Down = Up = Below =\
        Above = Beside = Under = Around = Underneath = Along =\
        Left = Right = North = South = Over= 4, #- spaced direction relation
    On = Onto = Off = Against = 5, # contact relation
    Of = From = 6, # reference relation
    At = By = 7, # location relation
    Because = 8, # causal relation
    For = If = 9, # declare cause relation
    With = 10, #characteristic of frame or some object
    Through = 11, # usage
    IGNORE = 12 # add prepositions to ignore here.

class NODE_PROPERTIES(IntEnum):
    SUBJ = 0
    OBJ = 1
    QTY = 2
    MOD = 3
    MARK = 4
    NEG = 5
    ACTION = 6
    LOC = 7
    POS = 8
    PRP = 9
    LAST = 10 #Always keep LAST at the end

LOCATION_WORDS = ['on', 'in', 'above', 'below', 'under', 'top', 'back', 'behind', 'front', 'across', 'onto', 'into']

ROLE_PROPERTY_MAP = {ROLE_TYPE.SUBJ:NODE_PROPERTIES.SUBJ,
                     ROLE_TYPE.OBJ:NODE_PROPERTIES.OBJ,
                     ROLE_TYPE.NN_MOD:NODE_PROPERTIES.MOD,
                     ROLE_TYPE.JJ_MOD:NODE_PROPERTIES.MOD,
                     ROLE_TYPE.JJ_CLS:NODE_PROPERTIES.MOD,
                     ROLE_TYPE.CD:NODE_PROPERTIES.QTY,
                     ROLE_TYPE.MARK:NODE_PROPERTIES.MARK,
                     ROLE_TYPE.NEG:NODE_PROPERTIES.NEG,
                     ROLE_TYPE.VB_CLS:NODE_PROPERTIES.ACTION,
                     ROLE_TYPE.NN_POS:NODE_PROPERTIES.POS,
                     # Mapping prepositions
                     ROLE_TYPE.PRP:NODE_PROPERTIES.PRP,
                     ROLE_TYPE.PRP_MOD:NODE_PROPERTIES.MOD,
                     ROLE_TYPE.PRP_POS:NODE_PROPERTIES.POS
                     }

PREDICATE_PROPERTY_NAME = {NODE_PROPERTIES.SUBJ:"subj",
                           NODE_PROPERTIES.OBJ:"obj",
                           NODE_PROPERTIES.MOD:"mod",
                           NODE_PROPERTIES.QTY:"qty",
                           NODE_PROPERTIES.MARK:"mark",
                           NODE_PROPERTIES.NEG:"negated",
                           NODE_PROPERTIES.ACTION:"action",
                           NODE_PROPERTIES.LOC:"loc",
                           NODE_PROPERTIES.PRP:"prep",
                           NODE_PROPERTIES.POS:"poss"}

PREPOSITION_CATEGORY_NAME = {
    In_Type.Before:"Event Before", # before time
    In_Type.After:"Event After", # after time
    In_Type.As:"Event Simulatenous",
    In_Type.In:"Subsume Relation", #subsume relation
    In_Type.Across:"Spaced Relation", #- spaced direction relation
    In_Type.On:"Contact Relation", # contact relation
    In_Type.Of:"Reference Relation", # reference relation
    In_Type.At:"Location Relation", # location relation
    In_Type.Because:"Causal Relation", # causal relation
    In_Type.For:"Declare Relation", # declare cause relation
    In_Type.With:"Property Relation", #characteristic of frame or some object
    In_Type.Through:"Usage Relation",
    In_Type.IGNORE:"Unknown Relation"
}

class roleObject():
    def __init__(self, annotText):
        annotTextTokens = annotText.split("\t")

        self.Id = int(annotTextTokens[SRL_TAGS.ID])
        self.word = re.split('[, .]',annotTextTokens[SRL_TAGS.WORD])[0]
        self.pos = annotTextTokens[SRL_TAGS.POS]
        self.parentId = int(annotTextTokens[SRL_TAGS.DEP])
        self.ud = annotTextTokens[SRL_TAGS.UDR]

        self.frameList = []
        self.roleType = -1
        self.inType = -1
        self.analyzeRole()

    def __hash__(self):
        return hash((self.Id, self.pos, self.ud))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.Id == other.Id and self.word == other.word

    def analyzeRole(self):
        if 'ROOT' in self.ud:
            self.roleType = ROLE_TYPE.ROOT
        elif 'subj' in self.ud:
            self.roleType = ROLE_TYPE.SUBJ
            if 'pass' in self.ud:
                self.roleType = ROLE_TYPE.OBJ
        elif 'obj' in self.ud or 'ccomp' in self.ud:
            self.roleType = ROLE_TYPE.OBJ
            if 'pass' in self.ud:
                self.roleType = ROLE_TYPE.SUBJ
        # elif 'xcomp' in self.ud:
        #     self.roleType = ROLE_TYPE.SUBJ
        elif 'acl' in self.ud or 'advcl' in self.ud:
            if 'VB' in self.pos:
                self.roleType = ROLE_TYPE.VB_CLS
            elif 'JJ' in self.pos:
                self.roleType = ROLE_TYPE.JJ_CLS
        elif 'mod' in self.ud:
            if 'num' in self.ud:
                self.roleType = ROLE_TYPE.CD
            elif 'poss' in self.ud:
                self.roleType = ROLE_TYPE.NN_POS
            elif 'JJ' in self.pos:
                self.roleType = ROLE_TYPE.JJ_MOD
            elif 'NN' in self.pos:
                self.roleType = ROLE_TYPE.NN_MOD
        elif 'aux' in self.ud:
            self.roleType = ROLE_TYPE.AUX
            # self.analyzeAuxType()
        elif 'conj' in self.ud:
            self.roleType = ROLE_TYPE.CONJ
        elif 'mark' in self.ud:
            self.roleType = ROLE_TYPE.MARK
        elif 'compound' in self.ud or 'det' in self.ud or 'cc' in self.ud or 'POS' in self.pos:
            self.roleType = ROLE_TYPE.COMP
            if 'prt' in self.ud or 'POS' in self.pos:
                self.roleType = ROLE_TYPE.COMP_PRT
        elif 'neg' in self.ud:
            self.roleType = ROLE_TYPE.NEG

        if 'IN' is self.pos:
            self.analyzeInType()

    def analyzeInType(self):
        if self.word.lower() == 'before': # before time
            self.inType = In_Type.Before
        elif self.word.lower() == 'after': # after time
            self.inType = In_Type.After # after time
        elif self.word.lower() in ['as','while']: # parallel same time
            self.inType = In_Type.As
        elif self.word.lower() in ['in','into','among','within','inside']:
            self.inType = In_Type.In
        elif self.word.lower() in ['across','behind','outside','out',
            'down','up','below','above','beside', 'under', 'around',
            'underneath', 'along', 'left', 'right', 'north', 'south']: # spaced direction relation
            self.inType = In_Type.Across
        elif self.word.lower() in ['on', 'onto', 'off', 'against']: # contact relation
            self.inType = In_Type.On
        elif self.word.lower() in ['of','from']: # reference relation
            self.inType = In_Type.Of
        elif self.word.lower() in ['at', 'by']: # location relation
            self.inType = In_Type.At
        elif self.word.lower() == 'because': # causal relation
            self.inType = In_Type.Because
        elif self.word.lower() in ['for', 'if']: # declarative relation
            self.inType = In_Type.For
        elif self.word.lower() == 'with': #characteristic of frame or some object
            self.inType = In_Type.With
        elif self.word.lower() == 'through': # usage
            self.inType = In_Type.Through
        elif self.word.lower() in ['over']: # append other prepositions to ignore here.
            self.inType = In_Type.IGNORE

class predicateNode():
    def __init__(self, roleObj):
        self.role = roleObj
        self.depList = []
        self.properties = [[] for x in range(NODE_PROPERTIES.LAST)]

    def addDependentPredicates(self,depPredList):
        for pred in depPredList:
            self.depList.append(pred)

    def extractPropertiesFromDependentPredicates(self):
        # return back if the properties were already extracted
        for x in self.properties:
            if len(x) >0:
                return

        for predicate in self.depList:
            if not predicate.role.roleType in ROLE_PROPERTY_MAP.keys():
                continue
            nodePropertyVal = ROLE_PROPERTY_MAP[predicate.role.roleType]

            if nodePropertyVal == NODE_PROPERTIES.NEG:
                self.properties[nodePropertyVal].append("neg")
            else:
                # if the current predicate is not a subject or root then a verb in it's dependents can't be ACTION
                if nodePropertyVal == NODE_PROPERTIES.ACTION and \
                        not (self.role.roleType == ROLE_TYPE.SUBJ or self.role.roleType == ROLE_TYPE.ROOT):
                    continue

                for locWrd in LOCATION_WORDS:
                    if locWrd in predicate.role.word.split("_"):
                        nodePropertyVal = NODE_PROPERTIES.LOC
                        break
                self.properties[nodePropertyVal].append(predicate.role.word)

    def linkCompoundPredicates(self):
        mergedPredicateList = []

        predicateList = self.depList
        if len(predicateList) > 0:
            predicateList.sort(key=lambda x: x.role.Id)
            mergeCandidates = []
            previousRoleType = None
            for predicate in predicateList:
                # keep inserting into the list if the consecutive elements are of type COMP
                if predicate.role.roleType == ROLE_TYPE.COMP:
                    if not previousRoleType == ROLE_TYPE.COMP: # this is just for extra caution
                        mergeCandidates = []
                    mergeCandidates.append(predicate)
                else:
                    # when a non-compound word is seen, get a merged role containing the previous words
                    mergedWord = ""
                    mergedDependents = []

                    for candidate in mergeCandidates:
                        mergedWord +=  candidate.role.word + "_"
                        mergedDependents += candidate.depList
                    # if last candidate's id is one before the current one then merge
                    if len(mergeCandidates) > 0:
                        if mergeCandidates[-1].role.Id + 1 == predicate.role.Id:
                            predicate.role.word = mergedWord + predicate.role.word
                            predicate.addDependentPredicates(mergedDependents)
                        # otherwise see if the current parent id one greater.
                        elif mergeCandidates[-1].role.Id + 1 == self.role.Id:
                            self.role.word = mergedWord + self.role.word
                            self.addDependentPredicates(mergedDependents)
                        else:
                            print("Oops! Leaving out the compound words:{}".format(mergedWord))
                    mergeCandidates = []
                    mergedPredicateList.append(predicate)
                # don't forget to set the last seen predicate role type
                previousRoleType = predicate.role.roleType
            # if the last predicate in the dependent list was a compound type and wasn't merged yet
            if len(mergeCandidates)>0 and previousRoleType == ROLE_TYPE.COMP:
                mergedWord = ""
                mergedDependents = []
                for i in range(len(mergeCandidates)):
                    candidate = mergeCandidates[i]
                    mergedWord += candidate.role.word
                    if not i == len(mergeCandidates) - 1:
                        mergedWord += "_"
                    mergedDependents += candidate.depList
                if mergeCandidates[-1].role.Id + 1 == self.role.Id:
                    self.role.word = mergedWord + "_" + self.role.word
                    self.addDependentPredicates(mergedDependents)
                elif self.role.Id + 1 == mergeCandidates[0].role.Id:
                    self.role.word = self.role.word + "_" + mergedWord
                    self.addDependentPredicates(mergedDependents)
                else:
                    print("Oops! Leaving out the compound words:{}".format(mergedWord))

            else:
                self.depList = mergedPredicateList