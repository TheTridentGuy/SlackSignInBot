import requests
import datetime
import slack_sdk
import traceback
import flask
from flask import render_template
from slackeventsapi import SlackEventAdapter
import json
import pathlib
import gsheets
from pathlib import Path
from config import bot_token, secret, form_url, sheet_id, sheet_range, channel
from werkzeug.exceptions import HTTPException
import re


client = slack_sdk.WebClient(token=bot_token)
app = flask.Flask(__name__)
events = SlackEventAdapter(secret, "/slack/events", app)
data_file = Path(__file__).parent.resolve()/Path("data.json")
user_data = {}
if pathlib.Path(data_file).exists():
    user_data = json.load(open(data_file, "r"))


client.chat_postMessage(channel=channel, text=":cardinalpog: Sign-in bot is online!")


def report(message):
    client.chat_postMessage(channel=channel, text=message)
    return message


def hint(text):
    if text:
        return f"\nHINT: you don't need to provide any extra info (i.e. an email) to this command."
    return ""


@app.route("/")
def index():
    return render_template("index.html", form_url=form_url)


@app.route("/commands/register", methods=["POST"])
def register():
    user = flask.request.values.get("user_id")
    email = flask.request.values.get("text")
    user_data[user] = email
    json.dump(user_data, open(data_file, "w"))
    report(f":information_source: <@{user}> registered email {email}")
    if not re.match(r"^[^@+]+(\+[^@]+)?@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", email):
        report(f":warning: <@{user}> attempted to register invalid email '{email}'")
        return f":x: '{email}' does not appear to be a valid email, please try again."
    return f":white_check_mark: Registered your email as {email}. You may now sign in/out with /signin, or check your status with /signin-status"


@app.route("/commands/signin", methods=["POST"])
def signin():
    user = flask.request.values.get("user_id")
    email = user_data.get(user)
    if not email:
        report(f":information_source: <@{user}> tried to sign in without registering")
        return f":x: Please register your email with /signin-register [email]"
    try:
        data = get_signin_status(email)
        response = requests.post(f"{form_url}/formResponse?emailAddress={email}")
        if response.status_code == 200:
            return f":white_check_mark: Sucessfully submitted form with email {email}, you are now signed {'out' if data else 'in'}." + hint(flask.request.values.get("text"))
        else:

            return report(f":x: Unknown error submitting form with email '{email}', http status: {response.status_code}")
    except Exception as e:
        report(f":x: Unknown error signing in/out with email '{email}', {e}")
        return f":x: Something went wrong singing in/out with email {email}, please use the form ({form_url}/viewform) for now."



@app.route("/commands/status", methods=["POST"])
def status():
    user = flask.request.values.get("user_id")
    email = user_data.get(user)
    if not email:
        report(f"<@{user}> tried to check status without registering")
        return f":x: Please register your email with /sregister [email]"
    try:
        data = get_signin_status(email)
        if get_signin_status(email):
            return f":information_source: {data[0]} {data[1]} ({email}) has been in since {data[3]}" + hint(flask.request.values.get("text"))
        else:
            return f":information_source: {email} is currently signed out" + hint(flask.request.values.get("text"))
    except Exception as e:
        report(f":x: Unknown error checking status with email '{email}', {e}")
        return f":x: Something went wrong checking status with email {email}, please check the (https://docs.google.com/spreadsheets/d/{sheet_id}) sheet for now."


@app.errorhandler(HTTPException)
def handle_exception(e):
    headers = str(flask.request.headers).strip()
    data = flask.request.data.decode("utf-8").strip()
    method = flask.request.method
    path = flask.request.path
    http_version = flask.request.environ.get("SERVER_PROTOCOL", "HTTP/1.1")
    report(f":x: [{datetime.datetime.now()}] {e.code} {e.description}"
           + (f"\n\n-- TRACEBACK: --\n\n{traceback.format_exc().strip()}" if e.code == 500 else "")
           + f"\n\n-- REQUEST: --\n\n{method} {http_version} {path}"
           + (f"\n\n-- REQUEST HEADERS: --\n\n{headers}" if headers else "")
           + (f"\n\n-- REQUEST DATA: --\n\n{data}" if data else ""))
    return ":x: Something went wrong, please try again later."


def get_signin_status(email):
    data = gsheets.get_range(sheet_id, sheet_range)[1:]  # account for headers
    for entry in data:
        if entry[2] == email:
            return entry
    return False


if __name__ == "__main__":
    app.run("localhost", port=8080, debug=True)
