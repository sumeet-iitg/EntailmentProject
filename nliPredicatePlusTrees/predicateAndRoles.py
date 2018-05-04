
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
    ROOT_VERB = 0
    SUBJ = 1
    OBJ = 2
    CLAUSE = 3
    MOD = 4
    CONJ = 5
    MARK = 6
    AUX = 7
    COMP = 8
    CD = 9
    NEG = 10

class NODE_PROPERTIES(IntEnum):
    SUBJ = 0
    OBJ = 1
    QTY = 2
    MOD = 3
    MARK = 4
    NEG = 5
    ACTION = 6
    LOC = 7
    LAST = 8 #Always keep LAST at the end

LOCATION_WORDS = ['on', 'in', 'above', 'below', 'under', 'top', 'back', 'behind', 'front', 'across', 'onto', 'into']

ROLE_PROPERTY_MAP = {ROLE_TYPE.SUBJ:NODE_PROPERTIES.SUBJ,
                     ROLE_TYPE.OBJ:NODE_PROPERTIES.OBJ,
                     ROLE_TYPE.MOD:NODE_PROPERTIES.MOD,
                     ROLE_TYPE.CD:NODE_PROPERTIES.QTY,
                     ROLE_TYPE.MARK:NODE_PROPERTIES.MARK,
                     ROLE_TYPE.NEG:NODE_PROPERTIES.NEG,
                     ROLE_TYPE.ROOT_VERB:NODE_PROPERTIES.ACTION}

PREDICATE_PROPERTY_NAME = {NODE_PROPERTIES.SUBJ:"subj",
                           NODE_PROPERTIES.OBJ:"obj",
                           NODE_PROPERTIES.MOD:"mod",
                           NODE_PROPERTIES.QTY:"qty",
                           NODE_PROPERTIES.MARK:"mark",
                           NODE_PROPERTIES.NEG:"negated",
                           NODE_PROPERTIES.ACTION:"action",
                           NODE_PROPERTIES.LOC:"loc"}

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
        self.analyzeRole()

    def __hash__(self):
        return hash((self.Id, self.pos, self.ud))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.Id == other.Id and self.word == other.word

    def analyzeRole(self):
        if 'ROOT' in self.ud or 'VB' in self.pos and not 'aux' in self.ud:
            self.roleType = ROLE_TYPE.ROOT_VERB
        elif 'subj' in self.ud:
            self.roleType = ROLE_TYPE.SUBJ
            if 'pass' in self.ud:
                self.roleType = ROLE_TYPE.OBJ
        elif 'obj' in self.ud or 'ccomp' in self.ud:
            self.roleType = ROLE_TYPE.OBJ
            if 'pass' in self.ud:
                self.roleType = ROLE_TYPE.SUBJ
        elif 'xcomp' in self.ud:
            self.roleType = ROLE_TYPE.SUBJ
        elif 'acl' in self.ud or 'advcl' in self.ud:
            self.roleType = ROLE_TYPE.CLAUSE
        elif 'mod' in self.ud:
            self.roleType = ROLE_TYPE.MOD
            if self.ud == "nummod":
                self.roleType = ROLE_TYPE.CD
        elif 'aux' in self.ud:
            self.roleType = ROLE_TYPE.AUX
        elif 'conj' in self.ud :
            self.roleType = ROLE_TYPE.CONJ
        elif 'mark' in self.ud:
            self.roleType = ROLE_TYPE.MARK
        elif 'compound' in self.ud or 'det' in self.ud or 'cc' in self.ud or 'case' in self.ud:
            self.roleType = ROLE_TYPE.COMP
        elif 'neg' in self.ud:
            self.roleType = ROLE_TYPE.NEG

class predicateNode():
    def __init__(self, roleObj):
        self.role = roleObj
        self.depList = []
        self.properties = [None for x in range(NODE_PROPERTIES.LAST)]

    def addDependentPredicates(self,depPredList):
        for pred in depPredList:
            self.depList.append(pred)

    def extractPropertiesFromDependentPredicates(self):
        for predicate in self.depList:
            if not predicate.role.roleType in ROLE_PROPERTY_MAP.keys():
                continue
            nodePropertyVal = ROLE_PROPERTY_MAP[predicate.role.roleType]
            if nodePropertyVal == NODE_PROPERTIES.NEG:
                self.properties[nodePropertyVal] = "neg"
            else:
                for locWrd in LOCATION_WORDS:
                    if locWrd in predicate.role.word.split("_"):
                        nodePropertyVal = NODE_PROPERTIES.LOC
                self.properties[nodePropertyVal] = predicate.role.word

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