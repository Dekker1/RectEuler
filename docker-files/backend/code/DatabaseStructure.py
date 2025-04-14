import mongoengine as me
from enum import Enum


class OptimizationResult(me.EmbeddedDocument):
    strategy = me.StringField()
    layout = me.IntField()
    optimizationStep = me.IntField()
    rects = me.ListField(me.DictField())
    intersections = me.DictField()
    stats = me.DictField()
    elementGroups = me.ListField(me.DictField())



class BinaryMatrix(me.EmbeddedDocument):
    header = me.ListField(me.StringField())
    firstCol = me.ListField(me.StringField())
    matrixData = me.ListField(me.ListField(me.BooleanField()))


class Image(me.EmbeddedDocument):
    imgdata = me.FileField()
    filename = me.StringField()


class Status(Enum):
    FINISHED = "FINISHED"
    RUNNING = "RUNNING"
    QUEUED = "QUEUED"


class DatasetSettings(me.Document):
    JobID = me.StringField(unique=True)
    isExample = me.BooleanField(default=False)
    ExampleDatasetName = me.StringField(required=False)
    email = me.EmailField(required=False)
    didSendMail = me.BooleanField(default=False)
    status = me.EnumField(Status, default=Status.QUEUED)
    expirationDate = me.DateField(required=True)
    creationDateTime = me.DateTimeField(required=True)
    token = me.StringField(required=True)
    images = me.EmbeddedDocumentListField(Image)
    results = me.EmbeddedDocumentListField(OptimizationResult)
    matrix = me.EmbeddedDocumentField(BinaryMatrix, required=True)
    configJSON = me.DictField(default=None)
    JSONKey = me.StringField()
