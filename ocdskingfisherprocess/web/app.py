from flask import Flask, request, render_template
from ocdskingfisherprocess.config import Config
from ocdskingfisherprocess.store import Store
from ocdskingfisherprocess.database import DataBase
from ocdskingfisherprocess.util import parse_string_to_date_time, parse_string_to_boolean
import tempfile
import os
import json

config = Config()
config.load_user_config()

app = Flask(__name__)


@app.route("/")
def hello():
    return "OCDS Kingfisher"


@app.route("/robots.txt")
def robots_txt():
    return "User-agent: *\nDisallow: /"


@app.route("/app")
def app_index():
    return render_template("app/index.html")


@app.route("/app/collection")
def app_collections():
    database = DataBase(config=config)
    return render_template("app/collections.html", collections=database.get_all_collections())


@app.route("/app/collection/<collection_id>")
def app_collection_index(collection_id):
    database = DataBase(config=config)
    collection = database.get_collection(collection_id)
    return render_template("app/collection/index.html", collection=collection)


@app.route("/app/collection/<collection_id>/file")
def app_collection_files(collection_id):
    database = DataBase(config=config)
    collection = database.get_collection(collection_id)
    files = database.get_all_files_in_collection(collection_id)
    return render_template("app/collection/files.html", collection=collection, files=files)


def _api_v1_check_authorization(request):
    api_key = request.headers.get('Authorization', '')[len('ApiKey '):]
    return api_key and api_key in config.web_api_keys


@app.route("/api/")
def api():
    return "OCDS Kingfisher APIs"


@app.route("/api/v1/")
def api_v1():
    return "OCDS Kingfisher APIs V1"


@app.route("/api/v1/submit/end_collection_store/", methods=['POST'])
def api_v1_submit_end_collection_store():
    if not _api_v1_check_authorization(request):
        return "ACCESS DENIED", 401

    # TODO check all required fields are there!

    database = DataBase(config=config)
    store = Store(config=config, database=database)

    collection_source = request.form.get('collection_source')
    collection_data_version = parse_string_to_date_time(request.form.get('collection_data_version'))
    collection_sample = parse_string_to_boolean(request.form.get('collection_sample', False))

    store.load_collection(
        collection_source,
        collection_data_version,
        collection_sample,
    )

    if store.is_collection_store_ended():
        return "OCDS Kingfisher APIs V1 Submit - Already Done!"
    else:
        store.end_collection_store()
        return "OCDS Kingfisher APIs V1 Submit"


@app.route("/api/v1/submit/file/", methods=['POST'])
def api_v1_submit_file():
    if not _api_v1_check_authorization(request):
        return "ACCESS DENIED", 401

    # TODO check all required fields are there!

    database = DataBase(config=config)
    store = Store(config=config, database=database)

    collection_source = request.form.get('collection_source')
    collection_data_version = parse_string_to_date_time(request.form.get('collection_data_version'))
    collection_sample = parse_string_to_boolean(request.form.get('collection_sample', False))

    store.load_collection(
        collection_source,
        collection_data_version,
        collection_sample,
    )

    file_filename = request.form.get('file_name')
    file_url = request.form.get('url')
    file_data_type = request.form.get('data_type')
    file_encoding = request.form.get('encoding', 'utf-8')

    if 'file' in request.files:

        (tmp_file, tmp_filename) = tempfile.mkstemp(prefix="ocdskf-")
        os.close(tmp_file)

        request.files['file'].save(tmp_filename)

        store.store_file_from_local(file_filename, file_url, file_data_type, file_encoding, tmp_filename)

        os.remove(tmp_filename)

    elif 'local_file_name' in request.form:

        store.store_file_from_local(file_filename, file_url, file_data_type, file_encoding, request.form.get('local_file_name'))

    else:

        raise Exception('Did not send file data')

    return "OCDS Kingfisher APIs V1 Submit"


@app.route("/api/v1/submit/item/", methods=['POST'])
def api_v1_submit_item():
    if not _api_v1_check_authorization(request):
        return "ACCESS DENIED", 401

    # TODO check all required fields are there!

    database = DataBase(config=config)
    store = Store(config=config, database=database)

    collection_source = request.form.get('collection_source')
    collection_data_version = parse_string_to_date_time(request.form.get('collection_data_version'))
    collection_sample = parse_string_to_boolean(request.form.get('collection_sample', False))

    store.load_collection(
        collection_source,
        collection_data_version,
        collection_sample,
    )

    file_filename = request.form.get('file_name')
    file_url = request.form.get('url')
    file_data_type = request.form.get('data_type')
    item_number = int(request.form.get('number'))

    data = json.loads(request.form.get('data'))

    store.store_file_item(
        file_filename,
        file_url,
        file_data_type,
        data,
        item_number,
    )

    return "OCDS Kingfisher APIs V1 Submit"


@app.route("/api/v1/submit/file_errors/", methods=['POST'])
def api_v1_submit_file_errors():
    if not _api_v1_check_authorization(request):
        return "ACCESS DENIED", 401

    # TODO check all required fields are there!

    database = DataBase(config=config)
    store = Store(config=config, database=database)

    collection_source = request.form.get('collection_source')
    collection_data_version = parse_string_to_date_time(request.form.get('collection_data_version'))
    collection_sample = parse_string_to_boolean(request.form.get('collection_sample', False))

    store.load_collection(
        collection_source,
        collection_data_version,
        collection_sample,
    )

    file_filename = request.form.get('file_name')
    file_errors_raw = request.form.get('errors')
    file_errors = json.loads(file_errors_raw)
    file_url = request.form.get('url')

    store.store_file_errors(file_filename, file_url, file_errors)

    return "OCDS Kingfisher APIs V1 Submit"
