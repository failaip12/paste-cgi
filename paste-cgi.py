#!/usr/bin/env python3
import os
import sys
import random
import string
import json
from datetime import datetime, timezone, timedelta


CWD = os.getcwd()
DATABASE_DIRECTORY = os.path.join(CWD, "database_directory")
ALLOWED_TYPES = ["plain", "password"]
ALLOWED_EXPIRATIONS = [
    "never",
    "burn_after_read",
    "10_minutes",
    "1_hour",
    "1_day",
    "1_week",
    "2_weeks",
    "1_month",
    "6_months",
    "1_year",
]


class SubmitConstants:
    TYPE: str = "type"
    TITLE: str = "title"
    TITLE_ENCRYPTED: str = "title_encrypted"
    EXPIRATION: str = "expiration"
    PASTED_TEXT: str = "pasted_text"
    DATE_CREATED: str = "date_created"


def convert(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def check_working_dir(allowed_dir):
    if allowed_dir is None or allowed_dir != CWD:
        print("Content-Type: text/plain")
        print("")
        print("NOT ALLOWED DIRECTORY")
        sys.exit(0)


def status_405():
    print("Status: 405 Method Not Allowed")
    print("Content-Type: text/plain")
    print("")
    print("405 Method Not Allowed")
    sys.exit(0)


def status_415():
    print("Status: 415 Unsupported Media Type")
    print("Content-Type: text/plain")
    print("")
    print("415 Unsupported Media Type.")
    sys.exit(0)


def status_404():
    print("Status: 404 Not Found")
    print("Content-Type: text/plain")
    print("")
    print("File not found")
    sys.exit(0)


def check_method(method):
    if method not in ["GET", "POST"]:
        status_405()


def get_content_lenght():
    temp_len = os.environ.get("CONTENT_LENGTH", None)
    if temp_len is not None and temp_len.isdigit():
        return int(temp_len)
    return 0


def generate_random_string():
    return "".join(
        random.choices(
            string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16
        )
    )


def validate_payload(payload):
    if not isinstance(payload, dict):
        status_415()
    if SubmitConstants.TYPE not in payload or payload[SubmitConstants.TYPE] not in ALLOWED_TYPES:
        status_415()
    if SubmitConstants.TITLE_ENCRYPTED not in payload:
         status_415()
    if SubmitConstants.TITLE not in payload:
         status_415()
    if SubmitConstants.EXPIRATION not in payload or payload[SubmitConstants.EXPIRATION] not in ALLOWED_EXPIRATIONS:
        status_415()
    if SubmitConstants.PASTED_TEXT not in payload:
        status_415()
    


def submit(post_data):
    if not os.path.exists(DATABASE_DIRECTORY):
        os.makedirs(DATABASE_DIRECTORY)
    full_path = ""
    while True:
        random_id = generate_random_string()
        full_path = os.path.join(DATABASE_DIRECTORY, f"{random_id}.json")
        if not os.path.exists(full_path):
            break

    data = {
        SubmitConstants.TYPE: post_data.get(SubmitConstants.TYPE),
        SubmitConstants.TITLE: post_data.get(SubmitConstants.TITLE),
        SubmitConstants.TITLE_ENCRYPTED: post_data.get(SubmitConstants.TITLE_ENCRYPTED),
        SubmitConstants.EXPIRATION: post_data.get(SubmitConstants.EXPIRATION),
        SubmitConstants.PASTED_TEXT: post_data.get(SubmitConstants.PASTED_TEXT),
        SubmitConstants.DATE_CREATED: datetime.now(timezone.utc),
    }

    if None in data.values():
         status_415()

    try:
        with open(full_path, "w") as json_file:
            json.dump(data, json_file, indent=4, default=convert)
    except IOError as e:
        print("Status: 500 Internal Server Error")
        print("Content-Type: text/plain")
        print("")
        print(f"Error writing to file: {e}")
        sys.exit(1)

    print("Content-Type: application/json")
    print("")
    print(json.dumps({"id": random_id}))


def handle_data(data):
    expiry = data[SubmitConstants.EXPIRATION]
    date = datetime.fromisoformat(data[SubmitConstants.DATE_CREATED])
    date_now = datetime.now(timezone.utc)

    deleted = False
    delete_after_read = False

    if expiry == "never":
        pass
    elif expiry == "burn_after_read":
        deleted = False
        delete_after_read = True
    elif expiry == "10_minutes":
        if date + timedelta(minutes=10) <= date_now:
            deleted = True
    elif expiry == "1_hour":
        if date + timedelta(hours=1) <= date_now:
            deleted = True
    elif expiry == "1_week":
        if date + timedelta(weeks=1) <= date_now:
            deleted = True
    elif expiry == "2_weeks":
        if date + timedelta(weeks=2) <= date_now:
            deleted = True
    elif expiry == "1_month":
        if date + timedelta(days=30) <= date_now:
            deleted = True
    elif expiry == "6_months":
        if date + timedelta(days=180) <= date_now:
            deleted = True
    elif expiry == "1_year":
        if date + timedelta(days=365) <= date_now:
            deleted = True

    return delete_after_read, deleted


def return_paste(query_string):
    if query_string is None or not query_string.startswith("id="):
        status_415()

    parts = query_string.split("=")
    if len(parts) != 2 or not parts[1]:
        status_415()

    paste_id = parts[1]

    full_path = os.path.join(DATABASE_DIRECTORY, f"{paste_id}.json")
    directory = os.path.dirname(full_path)
    os.chdir(directory)

    if os.getcwd() != DATABASE_DIRECTORY:
        status_415()

    if not os.path.exists(full_path):
        status_404()

    with open(full_path, "r") as file:
        data = json.load(file)

    try:
        delete_after_read, deleted = handle_data(data)

        if deleted:
            os.remove(full_path)
            status_404()

        print("Content-Type: application/json")
        print("")
        print(json.dumps(data, default=convert))

        if delete_after_read:
            os.remove(full_path)

        sys.exit(0)
    except Exception:
        status_404()


allowed_dir = os.environ.get("ALLOWED_DIR", None)
check_working_dir(allowed_dir)

method = os.environ.get("REQUEST_METHOD", None)
check_method(method)

script_name = os.environ.get("SCRIPT_NAME", None)
query_string = os.environ.get("QUERY_STRING", None)

content_type = os.environ.get("CONTENT_TYPE", None)
content_length = get_content_lenght()


if method == "GET":
    if script_name == "/paste":
        return_paste(query_string)
elif method == "POST":
    post_data = sys.stdin.read(content_length)
    post_data = json.loads(post_data)
    if script_name == "/submit":
        validate_payload(post_data)
        submit(post_data)

sys.exit(0)
