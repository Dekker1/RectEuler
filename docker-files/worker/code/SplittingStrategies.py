import logging
import random

import numpy as np
import sklearn.cluster
import sklearn_extra.cluster
import scipy.spatial.distance
from typing import Dict, List, Iterable
from sklearn.utils import shuffle


def removeMaxElement(reduced):
    countDict = {}
    for k, v in reduced.items():
        for element in v:
            key = element
            if isinstance(key, (list, tuple)):
                key = tuple(key)
            if key not in countDict:
                countDict[key] = [k]
            else:
                countDict[key].append(k)
    maxCount = 0
    maxElement = None
    for k, v in countDict.items():
        if len(v) > maxCount:
            maxElement = k
            maxCount = len(v)

    setsToDeleteElementFrom = countDict[maxElement]
    for s in setsToDeleteElementFrom:
        if isinstance(maxElement, tuple):
            maxElement = list(maxElement)
        reduced[s].remove(maxElement)

    newdict = {}
    for s in setsToDeleteElementFrom:
        newdict[s] = [maxElement]
    return reduced, newdict


def removeAllMaxElement(reduced):
    countDict = {}
    for k, v in reduced.items():
        for element in v:
            key = element
            if isinstance(key, (list, tuple)):
                key = tuple(key)
            if key not in countDict:
                countDict[key] = [k]
            else:
                countDict[key].append(k)
    maxCount = 0
    maxElements = []
    for k, v in countDict.items():
        if len(v) > maxCount:
            maxElement = k
            maxCount = len(v)

    setsToDeleteElementFrom = countDict[maxElement]
    for s in setsToDeleteElementFrom:
        if isinstance(maxElement, tuple):
            maxElement = list(maxElement)
        reduced[s].remove(maxElement)

    newdict = {}
    for s in setsToDeleteElementFrom:
        newdict[s] = [maxElement]
    return reduced, newdict


def removeMaxSet(reduced):
    maxlen = 0
    maxKey = None
    removedDict = {}
    for k, v in reduced.items():
        if len(v) > maxlen:
            maxlen = len(v)
            maxKey = k

    removedDict[maxKey] = reduced[maxKey]
    del reduced[maxKey]
    return reduced, removedDict


def splitByDepth(reduced):
    elementGroupDict = {}
    countDict = {}
    returnDict = {}
    for i, (setName, elementGroups) in enumerate(reduced.items()):
        for elementGroup in elementGroups:
            if isinstance(elementGroup, list):
                elementGroup = tuple(elementGroup)
            if elementGroup in elementGroupDict:
                elementGroupDict[elementGroup].append(setName)

            else:
                elementGroupDict[elementGroup] = []
                elementGroupDict[elementGroup].append(setName)

    for elementGroup, sets in elementGroupDict.items():
        numberOfSetInclusions = len(sets)

        if numberOfSetInclusions not in countDict:
            countDict[numberOfSetInclusions] = []
        else:
            countDict[numberOfSetInclusions].append(elementGroup)

    for count, elementGroups in countDict.items():
        returnDict[count] = {}
        for elementGroup in elementGroups:
            sets = elementGroupDict[elementGroup]
            for s in sets:
                if s not in returnDict[count]:
                    returnDict[count][s] = []
                if isinstance(elementGroup, tuple):
                    elementGroup = list(elementGroup)
                returnDict[count][s].append(elementGroup)
    return returnDict.values()


def randomHalfSplit(reduced):
    countDict = {}
    for k, v in reduced.items():
        for element in v:
            key = element
            if isinstance(key, (list, tuple)):
                key = tuple(key)
            if key not in countDict:
                countDict[key] = [k]
            else:
                countDict[key].append(k)

    s = set()
    for k, v in reduced.items():
        for element in v:
            if isinstance(element, list):
                element = tuple(element)
            s.add(element)

    s = list(s)

    low_depth_list = []
    high_depth_list = []
    for k, v in countDict.items():
        if len(v) < 2:

            low_depth_list.append(k)
        else:
            high_depth_list.append(k)

    random.shuffle(high_depth_list)
    split = len(high_depth_list) // 2
    keepElements = high_depth_list[:split]
    removeElements = high_depth_list[split:]

    keepElements.extend(low_depth_list)

    keepDict = {}
    removeDict = {}
    for k, v in reduced.items():
        for element in v:
            if isinstance(element, list):
                element = tuple(element)

            if element in keepElements:
                if isinstance(element, tuple):
                    element = list(element)
                if k not in keepDict.keys():
                    keepDict[k] = []
                keepDict[k].append(element)

            if element in removeElements:
                if isinstance(element, tuple):
                    element = list(element)
                if k not in removeDict.keys():
                    removeDict[k] = []
                removeDict[k].append(element)
    return keepDict, removeDict


def clusterSplit(reduced, numberOfSublayouts=2, random_state=0, numTry=0):
    numberOfSets = len(reduced.keys())
    setNames = list(reduced.keys())
    elementGroupDict = {}
    for i, (setName, elementGroups) in enumerate(reduced.items()):
        for elementGroup in elementGroups:
            if isinstance(elementGroup, list):
                elementGroup = tuple(elementGroup)
            if elementGroup in elementGroupDict:
                elementGroupDict[elementGroup]["vector"][i] = 1
                elementGroupDict[elementGroup]["setnames"].append(setName)

            else:
                elementGroupDict[elementGroup] = {"vector": np.zeros(numberOfSets), "setnames": []}
                elementGroupDict[elementGroup]["vector"][i] = 1
                elementGroupDict[elementGroup]["setnames"].append(setName)

    toCluster = list(map(lambda x: x["vector"], elementGroupDict.values()))
    elelementGroups = list(elementGroupDict.keys())

    kmeans = sklearn_extra.cluster.KMedoids(n_clusters=numberOfSublayouts, random_state=random_state, init="k-medoids++", metric="jaccard")
    clusters = kmeans.fit_predict(toCluster)

    returnlist = [{} for _ in range(numberOfSublayouts)]

    for i, c in enumerate(clusters):
        stenameidxs = np.where(toCluster[i] == 1)[0].tolist()
        elementGroup = elelementGroups[i]
        if isinstance(elementGroup, tuple):
            elementGroup = list(elementGroup)
        d = returnlist[c]
        for idx in stenameidxs:
            name = setNames[idx]
            if name in d:
                d[name].append(elementGroup)
            else:
                d[name] = []
                d[name].append(elementGroup)

    if numTry > 3:
        return returnlist
    for obj in returnlist:
        sum = 0
        for _ in obj.values():
            sum += 1

        if sum <= 5:
            logging.info(f"Split again with new seed {random_state * 11}")
            return clusterSplit(reduced, numberOfSublayouts=numberOfSublayouts, random_state=random_state * 11, numTry=numTry + 1)

    return returnlist


def randomSplit(reduced, numberOfSublayouts=2, random_state=0):
    elementGroupDict = {}
    for i, (setName, elementGroups) in enumerate(reduced.items()):
        for elementGroup in elementGroups:
            if isinstance(elementGroup, list):
                elementGroup = tuple(elementGroup)
            if elementGroup in elementGroupDict:
                elementGroupDict[elementGroup]["setnames"].append(setName)

            else:
                elementGroupDict[elementGroup] = {"setnames": []}
                elementGroupDict[elementGroup]["setnames"].append(setName)
    splits = np.array_split(shuffle(list(elementGroupDict.keys()), random_state=random_state), numberOfSublayouts)

    returnlist = []

    for i, split in enumerate(splits):
        d = {}
        for elementGroup in split:
            setnames = elementGroupDict[elementGroup]["setnames"]
            if isinstance(elementGroup, tuple):
                elementGroup = list(elementGroup)
            for setname in setnames:
                if setname in d:
                    d[setname].append(elementGroup)
                else:
                    d[setname] = []
                    d[setname].append(elementGroup)
        returnlist.append(d)

    return returnlist


def combinesplits(splits: Iterable[Dict[str, Iterable]]):
    returndict: Dict[str, List] = {}
    for split in splits:
        for setName, elements in split.items():
            if setName in returndict:
                returndict[setName].extend(elements)
            else:
                returndict[setName] = list(elements)
    return returndict
