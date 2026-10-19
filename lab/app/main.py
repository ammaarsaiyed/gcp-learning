"""notes-api: the app you grow all week.

Day 2: GET /                -> proves it runs on Cloud Run (no other services needed)
Day 3: POST/GET /notes      -> Firestore; each new note is also published to Pub/Sub (if TOPIC is set)
       POST /upload         -> Cloud Storage (if BUCKET is set)
Day 4: GREETING env var     -> injected from Secret Manager, no code change

There are no credentials in this file. On Cloud Run the client libraries use the attached
service account through Application Default Credentials (ADC).
"""
import datetime
import json
import os
import uuid
from functools import cache

import google.auth
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename

app = Flask(__name__)


@cache
def project_id():
    return google.auth.default()[1]


@cache
def db():
    from google.cloud import firestore
    return firestore.Client()


@cache
def publisher():
    from google.cloud import pubsub_v1
    return pubsub_v1.PublisherClient()


@cache
def gcs():
    from google.cloud import storage
    return storage.Client()


@app.get("/")
def index():
    # K_SERVICE / K_REVISION are set by Cloud Run itself
    return jsonify(
        service=os.environ.get("K_SERVICE", "local"),
        revision=os.environ.get("K_REVISION", "local"),
        greeting=os.environ.get("GREETING", "hello from GCP week"),
    )


@app.post("/notes")
def create_note():
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()
    if not text:
        return jsonify(error='send JSON like {"text": "..."}'), 400
    note = {
        "id": uuid.uuid4().hex,
        "text": text,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db().collection("notes").document(note["id"]).set(note)
    topic = os.environ.get("TOPIC")
    if topic:
        path = publisher().topic_path(project_id(), topic)
        publisher().publish(path, json.dumps(note).encode()).result(timeout=10)
    return jsonify(note), 201


@app.get("/notes")
def list_notes():
    docs = db().collection("notes").order_by("created_at", direction="DESCENDING").limit(20).stream()
    return jsonify([d.to_dict() for d in docs])


@app.post("/upload")
def upload():
    bucket = os.environ.get("BUCKET")
    f = request.files.get("file")
    if not bucket or not f:
        return jsonify(error="set the BUCKET env var and send a multipart form field named 'file'"), 400
    name = f"uploads/{uuid.uuid4().hex}-{secure_filename(f.filename or 'file')}"
    gcs().bucket(bucket).blob(name).upload_from_file(f.stream, content_type=f.content_type)
    return jsonify(object=f"gs://{bucket}/{name}"), 201
