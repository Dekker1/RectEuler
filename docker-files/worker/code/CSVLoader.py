import json

import pandas as pd
import numpy as np
import glob
from typing import Dict, Optional

splitSize = 5000


def load(filepath, delimiter=','):
    files = glob.glob(filepath + "/*.csv")
    if len(files) > 1:
        raise ValueError(f"Too many .csv files in {filepath}. Expected 1 got {len(files)}.")

    if len(files) == 0:
        raise ValueError(f"Missing .csv files in {filepath}. Expected 1 got 0.")

    data = pd.read_csv(files[0], delimiter=delimiter)
    matrix = data.iloc[0:, 1:].astype('bool').to_numpy()
    SetNames = list(map(lambda x: str(x), list(data.columns.values)[1:]))
    PrimitiveNames = list(map(lambda x: str(x), data.iloc[:, 0].to_list()))

    return SetNames, PrimitiveNames, matrix


def loadConfig(filepath: str) -> Optional[Dict]:
    files = glob.glob(filepath + "/config.json")
    if len(files) > 1:
        raise ValueError(f"Too many .json files in {filepath}. Expected 1 got {len(files)}.")
    if len(files) == 1:
        with open(files[0], 'r') as f:
            return json.load(f)
    else:
        return None


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def reduce(SetNames, PrimitiveNames, matrix):
    returnDict = {}
    for s in SetNames:
        returnDict[s] = []
    unq, count = np.unique(matrix, axis=0, return_counts=True)
    repeated_groups = unq[count > 0]
    # repeated_groups = unq[count > 1]

    for repeated_group in repeated_groups:
        repeated_idx = np.argwhere(np.all(matrix == repeated_group, axis=1))
        a = repeated_idx.ravel()
        splitlist = chunks(a, splitSize)

        for l in splitlist:
            if len(l) > 1:
                nameList = [PrimitiveNames[i] for i in l]
            else:
                nameList = PrimitiveNames[l[0]]

            i = 0
            for value in matrix[l[0], :]:
                if value:
                    returnDict[SetNames[i]].append(nameList)
                i += 1

    return returnDict


def FAKEreduce(SetNames, PrimitiveNames, matrix):
    returnDict = {}
    for s in SetNames:
        returnDict[s] = []

    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            if matrix[row, col]:
                returnDict[SetNames[col]].append(PrimitiveNames[row])

    return returnDict
