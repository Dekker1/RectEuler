import json
import logging
from psycopg.rows import dict_row

#from Worker.Databse.DatabaseStructure import DatasetSettings, Status, BinaryMatrix

layoutid = 0
diagramID = 0


def default(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def saveDatabaseFromModel(pool, model, intersections, stats):

    rects = json.loads(json.dumps(model._boxes, default=default))
    elementGroups = json.loads(json.dumps(list(model._primitives.values()), default=default))

    intersections = json.loads(json.dumps(intersections, default=default))
    saveDatabase(pool, model._JobID, model._splittingStrategy, model._currentLayoutNumber, model._solutionCount, rects, elementGroups, intersections, stats)


def saveDatabase(pool, JobID: str, strategy: str, layout: int, optimizationStep: int, rects: dict, elementGroups: dict, intersections: dict, stats: dict):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO optimization_result("dataset_id", "strategy", "layout_number", "optimization_step", "rects","element_groups", "intersections", "stats") VALUES( (select "id" FROM dataset WHERE "job_id" = %s), %s, %s, %s, %s, %s, %s, %s)',
                    (JobID, strategy, layout, optimizationStep, json.dumps(rects), json.dumps(elementGroups),
                     json.dumps(intersections), json.dumps(stats)))
                #conn.commit()
    except:
        logging.exception("Error while saving result in database")


def saveDatabaseStatus(pool, JobID: str, status: str):
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE dataset SET status = %s where job_id = %s", (status, JobID))
                #conn.commit()
    except:
        logging.exception("Error while status of dataset in database")


#def getEmailAdress(JobID: str):
#    mongoengine.connect(MONGO_DB_NAME, username=MONGO_USER, password=MONGO_PASSWORD, host=MONGO_HOSTNAME, port=MONGO_PORT, alias='default')
#    dbResult = DatasetSettings.objects(JobID=JobID).first()
#    return dbResult.email


#def didSendMailSavdDB(JobID: str, didSendMail: bool):
#    mongoengine.connect(MONGO_DB_NAME, username=MONGO_USER, password=MONGO_PASSWORD, host=MONGO_HOSTNAME, port=MONGO_PORT, alias='default')
#    dbResult = DatasetSettings.objects(JobID=JobID).first()
#    dbResult.didSendMail = didSendMail
#    dbResult.save()


def saveStatusInformUser(pool, JobID: str, status: str):
    saveDatabaseStatus(pool, JobID, status)
    #email = getEmailAdress(JobID)
    #try:
        #send_email()

    #except Exception as ex:
        #logging.exception(f"Could not send E-Mail to {email}")
        #didSendMailSavdDB(JobID, False)

    #else:
        #didSendMailSavdDB(JobID, True)
