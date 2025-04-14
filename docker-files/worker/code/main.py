from enum import Enum
from typing import Optional, Tuple
import psycopg
import psycopg_binary

import psycopg_pool
from psycopg.rows import dict_row

from Box_gurobi import Box
from ElementGroup_gurobi import GurobiElementGroup
from SplittingStrategies import *

import CSVLoader as loader
from redis import Redis

from ModelConstraints import BoxBoxSubsetConstraints, setNameOverlapConstraints, BoxtoBoxDistance, BoxPrimitiveExclude, preventBoxOverlap
from sendmail import send_new_site_user_email
import numpy as np
from CalculateIntersectionStats import calculateEmptyIntersection
import gurobipy as gp
from gurobipy import GRB
import logging
from saveResults import saveDatabaseStatus, saveStatusInformUser, saveDatabaseFromModel
import os

POSTGRES_PASSWORD = ""

REDIS_PORT = os.environ['REDIS_PORT']
REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']
REDIS_KEY = os.environ['REDIS_KEY']
POSTGRES_HOSTNAME = os.environ['POSTGRES_HOSTNAME']
POSTGRES_PORT = os.environ['POSTGRES_PORT']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_DB = os.environ['POSTGRES_DB']


with open("/run/secrets/POSTGRES_PASSWORD") as f:
    POSTGRES_PASSWORD = f.read().strip()


conninfo = f'host={POSTGRES_HOSTNAME} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}'
pool = psycopg_pool.ConnectionPool(conninfo, max_size=1, min_size=1)


class ResultStatus(Enum):
    TIMEOUT_TO_FIRST_SOLUTION = "TIMEOUT_TO_FIRST_SOLUTION"
    TIMEOUT_OVERALL_RUNTIME = "TIMEOUT_OVERALL_RUNTIME"


def generateDiagram(SetNames, PrimitiveNames, matrix, JobID: str, splittingStrategyName: str = "recursiveclusterSplit",
                    seed: int = 0,
                    TimeLimit: int = 60, maxExecutionQuotaToFirstSolutionSeconds: int = 50,
                    config: Optional = None) -> int | ResultStatus:
    mainSetSystem = loader.reduce(SetNames, PrimitiveNames, matrix)
    primitiveIDs, boxIDs = generateIDs(mainSetSystem)

    timeSpendInfeasibleSols = 0
    maxExecutionTimeQuotaTotal = 600
    ExecutionTimeTotal = 0
    currentTimeLimit = min(TimeLimit, maxExecutionTimeQuotaTotal - ExecutionTimeTotal)
    model = generateModel(mainSetSystem, primitiveIDs, boxIDs, JobID, currentTimeLimit,
                          maxExecutionQuotaToFirstSolutionSeconds, splittingStrategy="noSplit", JSONConfig=config)
    saveDatabaseStatus(pool, model._JobID, 'RUNNING')

    model._timeSpendInfeasibleSols = timeSpendInfeasibleSols
    model.optimize(Callback)
    ExecutionTimeTotal += model.Runtime

    if model._solutionCount > 0:
        # Found solution, no need to further subdivide the dataset
        saveDatabaseStatus(pool, model._JobID, 'FINISHED')
        return model._currentLayoutNumber

    timeSpendInfeasibleSols = model.Runtime

    if splittingStrategyName not in ["recursiveclusterSplit", "randomSplit"]:
        raise ValueError(f"Given value {splittingStrategyName} not supported for splittingStrategyName")
    splittingStrategy = None
    if splittingStrategyName == "recursiveclusterSplit":
        splittingStrategy = clusterSplit
    if splittingStrategyName == "randomSplit":
        splittingStrategy = randomSplit

    numberOfSublayouts = 2
    splits_no_sol = None
    lastFeasibleModel = None

    while splits_no_sol is None or len(splits_no_sol) > 0:
        splits = splittingStrategy(mainSetSystem, numberOfSublayouts, seed)
        splits_no_sol = []
        for split in splits:
            currentTimeLimit = min(TimeLimit, maxExecutionTimeQuotaTotal - ExecutionTimeTotal)
            model = generateModel(split, primitiveIDs, boxIDs, JobID, currentTimeLimit,
                                  maxExecutionQuotaToFirstSolutionSeconds, splittingStrategy=splittingStrategyName,
                                  oldModel=lastFeasibleModel, JSONConfig=config)
            model._timeSpendInfeasibleSols = timeSpendInfeasibleSols
            model.optimize(Callback)
            ExecutionTimeTotal += model.Runtime
            if model._user_terminate_time_limit or model.Status == GRB.INFEASIBLE or model.Status == GRB.UNBOUNDED or model.Status == GRB.INF_OR_UNBD:
                splits_no_sol.append(split)
                timeSpendInfeasibleSols += model.Runtime
            else:
                lastFeasibleModel = model
        if len(splits) == len(splits_no_sol):
            # if none of the sub layouts has a feasible solution, increase the number of sublayouts and try again
            numberOfSublayouts += 1
        else:
            # if at least one of the sub layouts has a feasible solution, recombine the sub set systems without solution and try to split in 2 again.
            mainSetSystem = combinesplits(splits_no_sol)
            numberOfSublayouts = 2
    if ExecutionTimeTotal >= maxExecutionTimeQuotaTotal:
        saveStatusInformUser(pool, model._JobID, 'TIMEOUT')

    else:
        saveDatabaseStatus(pool, model._JobID, 'FINISHED')
        saveStatusInformUser(pool, model._JobID, 'FINISHED')

    return model._currentLayoutNumber


def generateIDs(reduced):
    primitiveIDs = {}
    boxIDs = {}
    pID = 0
    bID = 0
    for k, v in reduced.items():
        for primitive in v:
            if isinstance(primitive, list):
                primitive = tuple(sorted(primitive))

            if primitive not in primitiveIDs:
                primitiveIDs[primitive] = pID
                pID += 1
        boxIDs[k] = bID
        bID += 1

    return primitiveIDs, boxIDs


def generateModel(reduced, primitiveIDs, boxIDs, JobID: str, TimeLimit: int,
                  maxExecutionQuotaToFirstSolutionSeconds: int, splittingStrategy: Optional[str] = None,
                  oldModel: Optional[gp.Model] = None,
                  JSONConfig: Optional[Dict] = None) -> gp.Model:
    Boxes = []
    Primitives = {}

    model = gp.Model("RectEuler")

    model._user_terminate_time_limit = False
    model.Params.TimeLimit = TimeLimit
    model._currentStatistics = []
    model._solutionCount = 0
    model._maxExecutionQuotaToFirstSolutionSeconds = maxExecutionQuotaToFirstSolutionSeconds
    model._splittingStrategy = splittingStrategy

    model._JobID = JobID

    if oldModel is not None and oldModel._solutionCount > 0:
        model._currentLayoutNumber = oldModel._currentLayoutNumber + 1
        model._timeSpendInfeasibleSols = oldModel._timeSpendInfeasibleSols
    else:
        model._currentLayoutNumber = 0
        model._timeSpendInfeasibleSols = 0

    globalBox = (model.addVar(lb=0, name="Box_{}_{}".format('golbal', 'x1'), vtype=GRB.CONTINUOUS),
                 model.addVar(lb=0, name="Box_{}_{}".format('golbal', 'y1'), vtype=GRB.CONTINUOUS),
                 model.addVar(lb=0, name="Box_{}_{}".format('golbal', 'x2'), vtype=GRB.CONTINUOUS),
                 model.addVar(lb=0, name="Box_{}_{}".format('golbal', 'y2'), vtype=GRB.CONTINUOUS))

    model.addConstr(globalBox[0] == 0)
    model.addConstr(globalBox[1] == 0)

    z = model.addVar(lb=0, name="z", vtype=GRB.CONTINUOUS)
    model.addConstr((globalBox[2] - globalBox[3]) <= z)
    model.addConstr(-(globalBox[2] - globalBox[3]) <= z)

    for key, elements in reduced.items():
        if len(elements) != 0:
            boxID = boxIDs[key]
            box = Box(key, model, boxID)
            Boxes.append(box)
            for element in elements:
                if isinstance(element, list):
                    items = tuple(sorted(element))
                    el = element
                else:
                    items = element
                    el = [element]

                PrimitiveID = primitiveIDs[items]
                if items not in Primitives:
                    primitive = GurobiElementGroup(el, model, PrimitiveID, config=JSONConfig)
                    Primitives[items] = primitive
                else:
                    primitive = Primitives[items]
                primitive.BoxesContainedIn.append(box)
                box.addPrimitive(Primitives[items])
                logging.info("Added {} to {}".format(primitive.ID, box.name))

    totalMaxSize = 0

    for box in Boxes:
        model.addConstr(globalBox[0] <= box.corner_left[0])
        model.addConstr(globalBox[1] <= box.corner_left[1])
        model.addConstr(globalBox[2] >= box.corner_right[0])
        model.addConstr(globalBox[3] >= box.corner_right[1])

        totalMaxSize += box.textSize[0]

    for p in Primitives.values():
        p.setSizeConctraint()
        totalMaxSize += max(p.item.getSize()[0], p.item.getSize()[1])

    model.setObjective(
        gp.quicksum((b.corner_right[0] - b.corner_left[0]) + (b.corner_right[1] - b.corner_left[1]) for b in Boxes) + (
                globalBox[2] - globalBox[0]) + (globalBox[3] - globalBox[1]) + z)
    model._M = 2 * totalMaxSize

    model.Params.MIPGap = 0.000

    model._lastiter = -GRB.INFINITY
    model._lastnode = -GRB.INFINITY
    model._vars = globalBox
    model._boxes = Boxes
    model._primitives = Primitives
    # Add the required variables to the model
    BoxPrimitiveExcludeAddVariables(model, Primitives, Boxes)
    preventBoxOverlapAddVariables(model, Boxes)
    BoxtoBoxDistanceAddVariables(model, Boxes)
    setNameOverlapAddvars(model, Boxes)

    BoxBoxSubsetConstraints(model, Boxes)

    BoxPrimitiveExclude(model, Primitives, Boxes)
    setNameOverlapConstraints(model, Boxes)
    preventBoxOverlap(model, Boxes)

    BoxtoBoxDistance(model)

    return model


'''
Add the necessary Variables for the exclusion of en element from a rectangle
'''


def BoxPrimitiveExcludeAddVariables(model: gp.Model, Primitives: Dict[Tuple, GurobiElementGroup],
                                    Boxes: List[Box]) -> None:
    model._BoxPrimitiveExludeVars = {}
    for primitive in Primitives.values():
        for box in Boxes:

            if primitive in box.containedPrimitives:
                continue
            b1 = model.addVar(name="pb_left_{}_{}".format(primitive.ID, box.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b2 = model.addVar(name="pb_right_{}_{}".format(primitive.ID, box.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b3 = model.addVar(name="pb_left_2_{}_{}".format(primitive.ID, box.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b4 = model.addVar(name="pb_right_2_{}_{}".format(primitive.ID, box.ID), lb=0, ub=1, vtype=GRB.BINARY)
            model._BoxPrimitiveExludeVars[primitive.ID + "_" + box.ID] = b1, b2, b3, b4


def setNameOverlapAddvars(model: gp.Model, Boxes: List[Box]) -> None:
    model._setNameOverlapVars = {}
    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):

            p1 = Boxes[i]
            p2 = Boxes[j]

            if p1 == p2:
                continue

            b1 = model.addVar(name="bb_text_left_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b2 = model.addVar(name="bb_text_right_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b3 = model.addVar(name="bb_text_left_2_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b4 = model.addVar(name="bb_text_right_2_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            model._setNameOverlapVars[p1.ID + "_" + p2.ID] = b1, b2, b3, b4


def Callback(model: gp.Model, where: GRB.Callback) -> None:
    if where == GRB.Callback.MIP:
        time = model.cbGet(GRB.Callback.RUNTIME)
        if time > model._maxExecutionQuotaToFirstSolutionSeconds and model._solutionCount == 0:
            model._user_terminate_time_limit = True
            model.terminate()

    if where == GRB.Callback.MIPSOL:
        obj = model.cbGet(GRB.Callback.MIPSOL_OBJ)
        objbst = model.cbGet(GRB.Callback.MIPSOL_OBJBST)
        objbnd = model.cbGet(GRB.Callback.MIPSOL_OBJBND)
        nodecnt = model.cbGet(GRB.Callback.MIPSOL_NODCNT)
        solcnt = model.cbGet(GRB.Callback.MIPSOL_SOLCNT)
        time = model.cbGet(GRB.Callback.RUNTIME)
        gap = abs(objbst - objbnd) / abs(objbst)

        logging.info(f"Save new layout!")
        svgDict, JSONIntersections = calculateEmptyIntersection(model._boxes)
        stats = {'MIPSOL_OBJ': obj, 'GAP': gap, 'MIPSOL_OBJBST': objbst, 'MIPSOL_OBJBND': objbnd,
                 'MIPSOL_NODCNT': nodecnt, 'MIPSOL_SOLCNT': solcnt, 'RUNTIME': time,
                 'timeSpendInfeasibleSols': model._timeSpendInfeasibleSols}

        saveDatabaseFromModel(pool, model, JSONIntersections, stats)
        model._solutionCount += 1


# add the variables for the box distance constraints to the model.
def BoxtoBoxDistanceAddVariables(model, Boxes):
    model._BoxtoBoxDistanceVariables = {}

    for i in range(len(Boxes)):
        for j in range(i + 1, len(Boxes)):
            p1 = Boxes[i]
            p2 = Boxes[j]
            b1 = model.addVar(name="bb_left_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b2 = model.addVar(name="bb_right_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b3 = model.addVar(name="bb_left_2_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b4 = model.addVar(name="bb_right_2_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b5 = model.addVar(name="bb_right_3_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b6 = model.addVar(name="bb_right_4_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b7 = model.addVar(name="bb_right_5_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b8 = model.addVar(name="bb_right_6_{}_{}".format(p1.ID, p2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            model._BoxtoBoxDistanceVariables["{}_{}".format(p1.ID, p2.ID)] = [b1, b2, b3, b4, b5, b6, b7, b8]


def preventBoxOverlapAddVariables(model: gp.Model, Boxes: List[Box]) -> None:
    model._BoxOverlapVars = {}
    for i in range(len(Boxes)):
        for j in range(i, len(Boxes)):
            # continue
            box1 = Boxes[i]
            box2 = Boxes[j]

            # text if two sets share elements
            if bool(set(box1.containedPrimitives) & set(box2.containedPrimitives)):
                continue

            b1 = model.addVar(name="pp_left_{}_{}".format(box1.ID, box2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b2 = model.addVar(name="pp_right_{}_{}".format(box1.ID, box2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            b3 = model.addVar(name="pp_left_2_{}_{}".format(box1.ID, box2.ID), lb=0, ub=1, vtype=GRB.BINARY)
            b4 = model.addVar(name="pp_right_2_{}_{}".format(box1.ID, box2.ID), lb=0, ub=1, vtype=GRB.BINARY)

            model._BoxOverlapVars[box1.ID + "_" + box2.ID] = b1, b2, b3, b4


def connect_to_redis():
    r = Redis(REDIS_HOSTNAME, REDIS_PORT, retry_on_timeout=True)
    print("connected to REDIS")
    return r


def get_new_dataset(id: str):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("select matrix, config_json where id = %s", id)
            data = cur.fetchone()[0]
            conn.commit()

    return data


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    redis_connection = connect_to_redis()

    while True:
        try:
            _, id = redis_connection.brpop(REDIS_KEY)
            if id:
                id = id.decode("utf-8")
                print(f"new Dataset: {id}")

                try:
                    with pool.connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("SELECT matrix, config_json from dataset where job_id = %s", (id,))
                            data = cur.fetchone()
                            #conn.commit()

                            matrix, configJSON = data
                except:
                    logging.exception("Error while collecting data from database")

                setNames = matrix['header']
                elementNames = matrix['firstCol']
                matrix = np.array(matrix['matrix'])

                generateDiagram(setNames, elementNames, matrix, id, config=configJSON)

        except Exception as e:
            saveDatabaseStatus(pool, id, "ERROR")
            logging.exception("Error while optimizing Model")
