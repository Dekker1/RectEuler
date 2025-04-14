import hmac
import io
import json
import os
from functools import wraps
from pathlib import Path
import psycopg
import psycopg_binary
import psycopg_pool

from flask import Flask, request, send_from_directory, jsonify, send_file
from psycopg.rows import dict_row
from werkzeug.utils import secure_filename
from .forms.UploadForm import UploadForm
from werkzeug.datastructures import CombinedMultiDict
from redis import Redis
from .utils import generateID, get_docker_variables
import os

REDIS_PORT = os.environ['REDIS_PORT']
REDIS_HOSTNAME = os.environ['REDIS_HOSTNAME']

POSTGRES_HOSTNAME = os.environ['POSTGRES_HOSTNAME']
POSTGRES_PORT = os.environ['POSTGRES_PORT']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_DB = os.environ['POSTGRES_DB']

UPLOAD_FOLDER = '../uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'svg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['WTF_CSRF_ENABLED'] = False

REDIS_CLIENT = Redis(host=REDIS_HOSTNAME, port=REDIS_PORT)

POSTGRES_PASSWORD = ""

with open("/run/secrets/POSTGRES_PASSWORD") as f:
    POSTGRES_PASSWORD = f.read().strip()


conninfo = f'host={POSTGRES_HOSTNAME} port={POSTGRES_PORT} dbname={POSTGRES_DB} user={POSTGRES_USER} password={POSTGRES_PASSWORD}'

pool = psycopg_pool.ConnectionPool(conninfo)



def addToRedisQueue(data):
    try:
        REDIS_CLIENT.lpush("rectEuler", data)
    except ConnectionError as e:
        print("ERROR REDIS CONNECTION: {}".format(e))


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def token_required(f):
    @wraps(f)
    def decorator(id, *args, **kwargs):
        token = None
        if 'token' in request.args:
            token = request.args['token']

        if not token:
            return jsonify({'message': 'a valid token is missing'}), 401

        try:
            with pool.getconn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT token from dataset where job_id = %s", (id))
                    data = cur.fetchone()
                    conn.commit()
            if not hmac.compare_digest(data.token, token):
                return jsonify({'message': 'token is invalid'}), 401

        except:
            return jsonify({'message': 'token is invalid'}), 401

        return f(id, *args, **kwargs)

    return decorator


@app.route('/deletedata/<string:id>', methods=['POST', "GET"])
@token_required
def deleteData(id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM dataset WHERE job_id = %s;", (id))
            cur.commit()

    return '', 200


@app.route('/getdata/<string:job_id>', methods=['POST', "GET"])
def getData(job_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select json_object_agg(agg_strategy.strategy, agg_strategy.layouts)from (select strategy, json_agg(agg_layout.single_result order by layout_number) as layouts from (select strategy, layout_number, json_agg(json_build_object('stats', stats, 'rects', rects, 'intersections', intersections, 'element_groups', element_groups) order by optimization_step) as single_result from optimization_result where dataset_id = (select id FROM dataset WHERE job_id = %s) group by strategy, layout_number) as agg_layout group by strategy) as agg_strategy",
                (job_id,))
            data = cur.fetchone()
    if len(data) > 0:
        return data[0], 200
    else:
        return '', 404


@app.route('/getstatus/<string:job_id>', methods=['POST', "GET"])
def getStatus(job_id):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "select status from dataset where job_id = %s", (job_id,))
            data = cur.fetchone()
            conn.commit()
    if data:
        return jsonify(data[0]), 200
    else:
        return '', 404


@app.route('/uploaddata', methods=['POST', "GET"])
def upload_data():
    form = UploadForm(CombinedMultiDict((request.files, request.form)))
    if not request.method == 'POST':
        return "", 405
    if not form.validate():
        return jsonify(form.errors), 422
    images = form.images.data
    email = None if form.email.data == "" else form.email.data
    CSV = form.CSV.data
    JSONKey = form.JSONKey.data
    ConfigJSON = form.configJSON.data
    id, token = generateID()

    save_to_db(id, token, CSV, ConfigJSON, JSONKey, email)
    addToRedisQueue(id)
    return jsonify({"id": id, "token": token}), 200


def save_to_db(job_id, token, matrix, config_json, json_key, email):
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "insert into dataset (job_id, token, matrix, config_json, json_key, email, status, creation_date_time, expiration_date) values (%s, %s, %s, %s, %s, %s, 'QUEUED', now(), (NOW() + interval '1 week'))",
                (job_id, token, json.dumps(matrix), config_json, json_key, email))
            conn.commit()
    return '', 200


def save_images(images, JobID: str):
    isExist = os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], JobID))
    if not isExist:
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], JobID))
    for image in images:
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], JobID, filename))


def delete_upload_directory(job_id: str):
    directory = secure_filename(job_id)
    path = os.path.join(app.config['UPLOAD_FOLDER'], directory)
    try:
        os.rmdir(path)
        print(f"Directory {directory} has been removed successfully")
    except OSError as error:
        print(f"Directory {directory} can not be removed")


@app.route('/image/<path:ID>/<path:filename>')
def getImage(ID, filename):
    path = Path("uploads") / ID
    return send_from_directory(path, filename, as_attachment=True)


@app.route('/examples/')
def getExamples():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "select dataset.job_id, dataset.dataset_name, json_agg(distinct o.strategy) as strategys from dataset join optimization_result o on dataset.id = o.dataset_id where is_example = true group by dataset.job_id, dataset.dataset_name")
            data = cur.fetchall()
    return data, 200


@app.route('/clean/')
def delete_expired():
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("delete from dataset where expiration_date < now() returning job_id")
            data = cur.fetchall()
    for entry in data:
        delete_upload_directory(entry['job_id'])
    return '', 200


if __name__ == '__main__':
    # app.run(port=80, host='0.0.0.0',)
    app.run()
