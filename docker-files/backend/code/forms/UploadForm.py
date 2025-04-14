import numbers
from collections import abc

from flask_wtf import FlaskForm
from werkzeug.datastructures import FileStorage
from wtforms import MultipleFileField, EmailField, StringField, ValidationError
from wtforms import validators, fields
import json

from wtforms.validators import StopValidation


# https://gist.github.com/dukebody/dcc371bf286534d546e9
class JSONField(fields.StringField):
    def _value(self):
        return json.dumps(self.data) if self.data else ''

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = json.loads(valuelist[0])
            except ValueError:
                raise ValueError('This field contains invalid JSON1')
        else:
            self.data = None

    def pre_validate(self, form):
        super().pre_validate(form)
        if self.data:
            try:
                json.dumps(self.data)
            except TypeError:
                raise ValueError('This field contains invalid JSON2')


class Images(object):
    def __init__(self, CSVField=None, JSONField=None, message=None):
        self.CSVField = CSVField
        self.JSONField = JSONField
        assert (CSVField and JSONField), "`CSVField` and `JSONField` must be specified."
        self.message = message

    def __call__(self, form, field):
        print(form)
        print(field)
        # raise ValidationError(self.message)


class CSVValidator(object):
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if field.data and (not isinstance(field.data, dict)):
            return

        for key in ["header", "matrix", "firstCol"]:
            if key not in field.data:
                raise ValidationError(f"Key {key} missing in CSV!")
        header = field.data["header"]
        matrix = field.data["matrix"]
        firstCol = field.data["firstCol"]

        if len(firstCol) != len(matrix):
            raise ValidationError(f"Number of rows in Matrix unequal to Elements in FirstCol")

        desiredLength = len(header)
        # for row in matrix:
    #     if len(row) != desiredLength:
    #         raise ValidationError(f"Number of elements in rows is different!")
    #    for value in row:
    #        if not isinstance(value, bool):
    #           raise ValidationError(f"Not all values in matrix are bool!")


class JSONConfigValidator(object):
    def __init__(self, CSVFieldName="CSV", ImagesFiledName="images", message=None):
        self.message = message
        self.CSVFieldName = CSVFieldName
        self.ImagesFiledName = ImagesFiledName

    def __call__(self, form, field):

        if self.CSVFieldName not in form:
            raise ValidationError(f"{self.CSVFieldName} missing in Form")

        if not field.data:
            return

        if field.data and (not isinstance(field.data, dict)):
            return

        for key in ["data", "settings"]:
            if key not in field.data:
                raise ValidationError(f"Key {key} missing JSON")

        for key in ["header", "matrix", "firstCol"]:
            if key not in form[self.CSVFieldName].data:
                raise ValidationError(f"Key {key} missing in CSV!")

        CSVKeys = sorted(form[self.CSVFieldName].data["firstCol"])
        JSONKeys = sorted(field.data["data"].keys())

        if CSVKeys != JSONKeys:
            raise ValidationError(f"Element Keys in JSON and {self.CSVFieldName} are not the same")

        for key in ["min-width", "min-height", "max-width", "max-height", "useScaling"]:
            if key not in field.data["settings"]:
                raise ValidationError(f"Field {key} missing in JSON settings!")

        for key in list(field.data["settings"].keys()):
            if key not in ["min-width", "min-height", "max-width", "max-height", "useScaling"]:
                del field.data["settings"][key]

        JSONKeyValues = []
        filesInJSON = []

        for key, value in field.data["data"].items():
            if "file" in value and form.JSONKey.data not in value and field.settings["useScaling"]:
                raise ValidationError(f"Field {form.JSONKey.data} missing in Object {key} in JSON")
            if "name" not in value:
                raise ValidationError(f"Field name missing in Object {key} in JSON")
            if "file" in value:
                filesInJSON.append(value["file"])

            if form.JSONKey.data in value:
                value["scaleValue"] = value[form.JSONKey.data]
            for key2 in list(value.keys()):
                if key2 not in ["name", "file", "scaleValue"]:
                    del value[key2]

            if "file" in value and "scaleValue" in value and not isinstance(value["scaleValue"], numbers.Number):
                raise ValidationError(f"Field {form.JSONKey.data} must be a number!")
            JSONKeyValues.append(value["scaleValue"])

        field.data["settings"]["min"] = min(JSONKeyValues)
        field.data["settings"]["max"] = max(JSONKeyValues)

        uploadedFilenames = []
        for file in form[self.ImagesFiledName].data:
            uploadedFilenames.append(file.filename)

        for fileInJSON in filesInJSON:
            if fileInJSON not in uploadedFilenames:
                raise ValidationError(f"{fileInJSON} missing in uploaded Files!")


class FilesSize:
    """Validates that the uploaded file is within a minimum and maximum
    file size (set in bytes).

    :param min_size: minimum allowed file size (in bytes). Defaults to 0 bytes.
    :param max_size: maximum allowed file size (in bytes).
    :param message: error message

    You can also use the synonym ``file_size``.
    """

    def __init__(self, max_size, max_total_size, min_size=0, min_total_size=0, message=None):
        self.min_size = min_size
        self.max_size = max_size
        self.max_total_size = max_total_size
        self.min_total_size = min_total_size
        self.message = message

    def __call__(self, form, field):

        if not (field.data and all(isinstance(x, FileStorage) and x for x in field.data)):
            return
        total_size = 0
        for data in field.data:
            file_size = len(data.read())
            total_size += file_size
            data.seek(0)  # reset cursor position to beginning of file

            if (file_size < self.min_size) or (file_size > self.max_size):
                # the file is too small or too big => validation failure
                raise ValidationError(
                    self.message
                    or field.gettext(
                        "File must be between {min_size} and {max_size} bytes.".format(
                            min_size=self.min_size, max_size=self.max_size
                        )
                    )
                )
        if (total_size < self.min_total_size) or (total_size > self.max_total_size):
            # the file is too small or too big => validation failure
            raise ValidationError(
                self.message
                or field.gettext(
                    "Sum of file sizes must be between {min_size} and {max_size} bytes.".format(
                        min_size=self.min_total_size, max_size=self.max_total_size
                    )
                )
            )


class FilesAllowed(object):
    """Validates that all the uploaded files are allowed by a given list of
    extensions or a Flask-Uploads :class:`~flaskext.uploads.UploadSet`.
    :param upload_set: A list of extensions or an
        :class:`~flaskext.uploads.UploadSet`
    :param message: error message
    You can also use the synonym ``files_allowed``.
    """

    def __init__(self, upload_set, message=None):
        self.upload_set = upload_set
        self.message = message

    def __call__(self, form, field):
        if not (field.data and all(isinstance(x, FileStorage) and x for x in field.data)):
            return

        for data in field.data:
            filename = data.filename.lower()

            if isinstance(self.upload_set, abc.Iterable):
                if any(filename.endswith('.' + x) for x in self.upload_set):
                    continue

                raise StopValidation(self.message or field.gettext(
                    'File does not have an approved extension: {extensions}'
                ).format(extensions=', '.join(self.upload_set)))

            if not self.upload_set.file_allowed(data, filename):
                raise StopValidation(self.message or field.gettext(
                    'File does not have an approved extension.'
                ))


class UploadForm(FlaskForm):
    images = MultipleFileField('images', validators=[validators.Optional(), FilesAllowed(['jpg', 'png', 'svg', 'jpeg'], 'Images only!'), FilesSize(max_size=1000000, max_total_size=10000000), Images("a", "b")])
    email = StringField("email", validators=[validators.Optional(), validators.Email()])
    CSV = JSONField("CSV", validators=[validators.DataRequired(), CSVValidator()])
    JSONKey = StringField("JSONKey", validators=[validators.Optional()])
    configJSON = JSONField("configJSON", validators=[validators.Optional(), JSONConfigValidator()])
