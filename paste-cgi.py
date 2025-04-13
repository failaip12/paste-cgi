#!/usr/bin/env python3
import os
import sys
import random
import string
import json


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
    EXPIRATION: str = "expiration"
    PASTED_TEXT: str = "pasted_text"


def check_working_dir(allowed_dir):
    if allowed_dir is None or allowed_dir != CWD:
        print("Content-Type: text/plain")
        print("")
        print("NOT ALLOWED DIRECTORY")
        sys.exit(0)


def check_method(method):
    if method not in ["GET", "POST"]:
        print("Status: 405 Method Not Allowed")
        print("Content-Type: text/plain")
        print("")
        print("405 Method Not Allowed")
        sys.exit(0)


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
    if (
        SubmitConstants.TYPE in payload
        and payload[SubmitConstants.TYPE] in ALLOWED_TYPES
    ):
        if SubmitConstants.TITLE in payload:
            if (
                SubmitConstants.EXPIRATION in payload
                and payload[SubmitConstants.EXPIRATION] in ALLOWED_EXPIRATIONS
            ):
                if SubmitConstants.PASTED_TEXT in payload:
                    return
    print("Status: 415 Unsupported Media Type")
    print("Content-Type: text/plain")
    print("")
    print("415 Unsupported Media Type: Expected 'application/json'.")
    sys.exit(0)


def return_index_html():
    try:
        with open("index.html", "r") as file:
            index_html = file.read()

        print("Content-Type: text/html")
        print("")
        print(index_html)

    except Exception:
        print("Status: 404 Not Found")
        print("Content-Type: text/html")
        print("")
        print("<html><body><h1>404 Not Found</h1></body></html>")


def return_pico_css():
    try:
        with open("pico.min.css", "r") as file:
            pico_css = file.read()

        print("Content-Type: text/css")
        print("")
        print(pico_css)

    except Exception:
        print("Status: 404 Not Found")
        print("Content-Type: text/html")
        print("")
        print("<html><body><h1>404 Not Found</h1></body></html>")


def return_favicon_svg():
    try:
        with open("favicon.svg", "r") as file:
            favicon_svg = file.read()

        print("Content-Type: image/svg+xml")
        print("")
        print(favicon_svg)

    except Exception:
        print("Status: 404 Not Found")
        print("Content-Type: text/html")
        print("")
        print("<html><body><h1>404 Not Found</h1></body></html>")


def submit(post_data):
    try:
        if not os.path.exists(DATABASE_DIRECTORY):
            os.makedirs(DATABASE_DIRECTORY)
        full_path = ""
        while True:
            random_id = generate_random_string()
            full_path = os.path.join(DATABASE_DIRECTORY, f"{random_id}.json")
            if not os.path.exists(full_path):
                break

        data = {
            SubmitConstants.TYPE: post_data[SubmitConstants.TYPE],
            SubmitConstants.TITLE: post_data[SubmitConstants.TITLE],
            SubmitConstants.EXPIRATION: post_data[SubmitConstants.EXPIRATION],
            SubmitConstants.PASTED_TEXT: post_data[SubmitConstants.PASTED_TEXT],
        }

        with open(full_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print("Content-Type: application/json")
        print("")
        print(json.dumps({"id": random_id}))
    except Exception as e:
        print("Content-Type: text/plain")
        print("")
        print(str(e))
        sys.exit(0)


allowed_dir = os.environ.get("ALLOWED_DIR", None)
check_working_dir(allowed_dir)

method = os.environ.get("REQUEST_METHOD", None)
check_method(method)

script_name = os.environ.get("SCRIPT_NAME", None)
query_string = os.environ.get("QUERY_STRING", None)

content_type = os.environ.get("CONTENT_TYPE", None)
content_length = get_content_lenght()


if method == "GET":
    if script_name == "/":
        return_index_html()
    elif script_name == "/pico.min.css":
        return_pico_css()
    elif script_name == "/favicon.svg":
        return_favicon_svg()
elif method == "POST":
    post_data = sys.stdin.read(content_length)
    post_data = json.loads(post_data)
    if script_name == "/submit":
        validate_payload(post_data)
        submit(post_data)

sys.exit(0)
