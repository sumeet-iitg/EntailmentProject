from ccg_nlpy import remote_pipeline
from nltk.corpus import framenet as fn
import codecs
import sys
import os
import re
from predicateAndRoles import roleObject, predicateNode, SRL_TAGS, ROLE_TYPE,NODE_PROPERTIES,PREDICATE_PROPERTY_NAME
from copy import deepcopy

'''
This file creates the roles and predicates out of a sentence. And contains the logic of making a predicate tree and extracting properties for the predicates.
'''

# pipeline = remote_pipeline.RemotePipeline()
# doc = pipeline.doc("The dog is coming out of the ocean.")

# try:
#     print(type(doc.get_srl_verb))
#     print(doc.get_srl_verb)
#     for predicate in doc.get_srl_verb:
#         lexicalUnit = predicate['properties']['predicate']
#         frameList = fn.frames_by_lemma(r'(?i){}'.format(lexicalUnit))
#         print(lexicalUnit + " : " + frameList)
#         # print(fn.frames(r'(?i){}'.format(predicateName)))
# except: pass

# try:
#     print(type(doc.get_srl_prep))
#     print(doc.get_srl_prep)
# except: pass


'''
1. Add root and clausal head Predicates first. 
2. Make a collection of nodes with common parents
Go thru the head Predicates. dependents of the head Predicates recursively add their dependents
 At the time of adding dependents, merge the compound types
5. In a separate pass through the predicate trees extract properties from the immediate dependents
'''
def makePredicateTree(roleList):

    commonParentListDict = {}

    print("=" * 89)
    print("Sentence to add frames for : {}".format(" ".join([role.word for role in roleList])))

    # In the first pass through the roles link the compound predicates
    previousRole = None
    linkedRoleList = []
    for role in roleList:
        if not previousRole is None:
            if previousRole.roleType == ROLE_TYPE.COMP or role.roleType == ROLE_TYPE.COMP_PRT:
                role.word = previousRole.word + "_" + role.word
                if role.roleType == ROLE_TYPE.COMP_PRT:
                    role.roleType = previousRole.roleType
                    role.parentId = previousRole.parentId
                    role.Id = previousRole.Id
                # remove the last inserted role because we are concatenating with the previous
                del linkedRoleList[-1]
        linkedRoleList.append(role)
        previousRole = role

    # Going through the roles, convert it to a predicate
    predicateDict = {}
    for role in linkedRoleList:
        predicateDict[role.Id] = predicateNode(role)

    for predicateId in predicateDict.keys():
        curPredicate = predicateDict[predicateId]
        if not curPredicate.role.parentId == 0:
            parentPredicate = predicateDict[curPredicate.role.parentId]
            parentPredicate.addDependentPredicates([curPredicate])

    # First get pointers to the head nodes of each predicate
    # for role in linkedRoleList:
    #     if role.parentId == 0 or role.roleType == ROLE_TYPE.ROOT_VERB or role.roleType == ROLE_TYPE.CLAUSE or role.roleType == ROLE_TYPE.MOD_POS:
    #         predicateTreeDict[role.Id] = predicateNode(role)

    # Add dependents for each of these head nodes
    # for predicateHead in predicateTreeDict.keys():
    #     for role in linkedRoleList:
    #         if role.parentId == predicateHead:
    #             predicateTreeDict[predicateHead].addDependentPredicates([predicateNode(role)])

    # Get roles with common parent together
    # for role in roleList:
    #     if role.parentId in commonParentListDict.keys():
    #         commonParentListDict[role.parentId].append(predicateNode(role))
    #     else:
    #         commonParentListDict[role.parentId] = [predicateNode(role)]

    # Start adding dependents for each of the predicates
    # for parentId in commonParentListDict.keys():
    #     if parentId in predicateTreeDict.keys():
    #         predicateTreeDict[parentId].addDependentPredicates(commonParentListDict[parentId])

    # Now, starting from the dependents of the head predicates, recursively add the sub-dependents
    # for predicateHead in predicateTreeDict.values():
    #     predicateHead.linkCompoundPredicates()
    #     dependentsToParse = [] + predicateHead.depList
    #
    #     while len(dependentsToParse) > 0:
    #         if dependentsToParse[0].role.Id in commonParentListDict.keys() and dependentsToParse[0].role.Id not in predicateTreeDict.keys():
    #             dependentsToParse[0].addDependentPredicates(commonParentListDict[dependentsToParse[0].role.Id])
    #             # merge the compound dependents here
    #             dependentsToParse[0].linkCompoundPredicates()
    #             # append a new set of dependents to parse
    #             dependentsToParse += dependentsToParse[0].depList
    #         del dependentsToParse[0]

    # recursively extract properties

    for predicateHead in predicateDict.values():

        predicateHead.extractPropertiesFromDependentPredicates()
        dependentsToExtract = predicateHead.depList

        for dependentPredicate in dependentsToExtract:
            # if there is a dependent conjunction predicate then join
            # with parent word if it doesn't have any more dependents
            if dependentPredicate.role.roleType == ROLE_TYPE.CONJ and len(dependentPredicate.depList) == 0:
                predicateHead.role.word = predicateHead.role.word + "_" + dependentPredicate.role.word

        while len(dependentsToExtract) > 0:
            dependentsToExtract[0].extractPropertiesFromDependentPredicates()
            dependentsToExtract += dependentsToExtract[0].depList
            del dependentsToExtract[0]

    # linkPrepositions(predicateDict)

    return predicateDict.values()

# def linkPrepositions(predicateDict):
#     for predicate in predicateDict.keys():
#         if predicate.role.roleType == ROLE_TYPE.IN:
#


def hasMatchingFrames(frameListA, frameListB):
    for frameA in frameListA:
        for frameB in frameListB:
            if frameA['ID'] == frameB['ID']:
                return True
    return False

class srlFileReader:
    def __init__(self, srlAnnotatedData):
        self.srlFileReader = codecs.open(srlAnnotatedData, 'r', encoding='utf-8')
        self.lineNum = 0

    def readSentenceAndAddFrame(self, roleObjects):
        print("=" * 89)
        print("Sentence to parse: {}".format(" ".join([role.word for role in roleObjects])))
        wordFrameDict = {}
        for line in self.srlFileReader:
            self.lineNum += 1
            # print("At line number {} in srlFile.".format(self.lineNum))
            if line == '\n' or line == '\r\n':
                break
            lineTokens = line.split("\t")
            if len(lineTokens) > SRL_TAGS.FRAME:
                if not lineTokens[SRL_TAGS.FRAME] == "_":
                    word = re.split('[, .]', lineTokens[SRL_TAGS.WORD])[0]
                    frameLU = re.split('[, .]', lineTokens[SRL_TAGS.FRAME])[0]
                    frameList = fn.frames_by_lemma(r'(?i){}'.format(frameLU))
                    if len(frameList) > 0:
                        wordFrameDict[word] = frameList
                        # print("Frame list for {}:{}".format(frameLU, frameList))

        for word in wordFrameDict.keys():
            for role in roleObjects:
                if role.word == word:
                    role.frameList = wordFrameDict[word]
                    print("Frame list for {}:{}".format(role.word, role.frameList))

def comparePredicateTrees(predicateTreeA, predicateTreeB):
    pass

def comparePredicateSets(predicateSetListA, predicateSetListB):
    matchingVerbFramePredicates= []
    for predSetA in predicateSetListA:
        for roleA in predSetA:
            if not roleA.isVerb or not len(roleA.frameList) > 0: continue
            for predSetB in predicateSetListB:
                for roleB in predSetB:
                    if not roleB.isVerb or not len(roleB.frameList) > 0: continue
                    if hasMatchingFrames(roleA.frameList, roleB.frameList):
                        matchingVerbFramePredicates.append((predSetA,predSetB))

    print("Candidate Predicates")
    for predList in [predicateSetListA, predicateSetListB]:
        for predSet in predList:
            print([role.word for role in predSet])

    if len(matchingVerbFramePredicates)>0:
        print("Matched Predicates:")
        for (predSetA,predSetB) in matchingVerbFramePredicates:
            print("{} ~= {}".format([role.word for role in predSetA],[role.word for role in predSetB]))
    else: print("No Matched Predicates")

def prettyPrintPredicateTree(predicateTree):

    for predicate in predicateTree:
        emptyProperty = True
        propertyString = " "
        for i in range(len(predicate.properties)):
            if len(predicate.properties[i]) > 0:
                propertyString += PREDICATE_PROPERTY_NAME[i] + ":" + ",".join(predicate.properties[i]) + " "
                emptyProperty = False

        if not emptyProperty:
            print("Predicate:{} \t Props:{}".format(predicate.role.word, propertyString))
        # subPredicates = [subPred for subPred in predicate.depList if not subPred.role.Id in predicateTree.keys()]

        # for subPred in subPredicates:
        #     print("-" * 40)
        #     print("Sub Predicate:{} \t Properties:{}".format(subPred.role.word, ",".join([PREDICATE_PROPERTY_NAME[i] + ":" + str(subPred.properties[i]) for i in range(len(subPred.properties)) if not subPred.properties[i] is None ])))
        #     print("-" * 40)
srlAnnotatedData = "C:\\Users\\Sumeet Singh\\Documents\\Lectures\\11-727\\Project\\path-lstm\\PathLSTM\\snli_1.0_test.spatial.sep.conll"
# depAnnotatedData = "C:\\Users\\Sumeet Singh\\Documents\\Lectures\\11-727\\Project\\path-lstm\\PathLSTM\\adjectiveDebug.txt"

depAnnotatedData = "C:\\Users\\Sumeet Singh\\Documents\\Lectures\\11-727\\Project\\path-lstm\\PathLSTM\\snli_1.0_test.spatial.sep.txt.conll"
# srlAnnotatedData = "C:\\Users\\Sumeet Singh\\Documents\\Lectures\\11-727\\Project\\path-lstm\\PathLSTM\\frames.txt"
# depAnnotatedData = "C:\\Users\\Sumeet Singh\\Documents\\Lectures\\11-727\\Project\\path-lstm\\PathLSTM\\dependency.txt"

# srlFileRdr = srlFileReader(srlAnnotatedData=srlAnnotatedData)

with codecs.open(depAnnotatedData, 'r', encoding='utf-8') as depReader:
    predicateTreePairList = []
    lineId = 0
    predicateTreePair = []
    roleObjects = []

    for line in depReader:
        if lineId < 2:
            if line == '\n' or line == '\r\n':
                # srlFileRdr.readSentenceAndAddFrame(roleObjects)
                predicateTree = makePredicateTree(roleObjects)
                prettyPrintPredicateTree(predicateTree)
                predicateTreePair.append(predicateTree)
                lineId += 1
                roleObjects = []
            else:
                roleObjects.append(roleObject(line))
        else:
            comparePredicateTrees(predicateTreePair[0], predicateTreePair[1])
            predicateTreePairList.append(predicateTreePair)
            roleObjects = [roleObject(line)] #insert the line read
            lineId = 0
            predicateTreePair = []
    predicateTreePairList.append(predicateTreePair)
    print(len(predicateTreePairList))
    # load the lexical units of MOTION frame
