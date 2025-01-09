import requests
import slack_sdk
import flask
from slackeventsapi import SlackEventAdapter
import json
import pathlib
import gsheets
from pathlib import Path
from config import bot_token, secret, form_url, sheet_id, sheet_range


client = slack_sdk.WebClient(token=bot_token)
app = flask.Flask(__name__)
events = SlackEventAdapter(secret, "/slack/events", app)
data_file = Path(__file__).parent.resolve()/Path("data.json")
user_data = {}
if pathlib.Path(data_file).exists():
    user_data = json.load(open(data_file, "r"))


@app.route("/commands/register", methods=["POST"])
def register():
    user = flask.request.values.get("user_id")
    email = flask.request.values.get("text")
    user_data[user] = email
    json.dump(user_data, open(data_file, "w"))
    return f":white_check_mark: Registered your email as {email}. You may now sign in/out with /signin, or check your status with /signin-status"


@app.route("/commands/signin", methods=["POST"])
def signin():
    user = flask.request.values.get("user_id")
    email = user_data.get(user)
    if not email:
        return f":x: Please register your email with /signin-register [email]"
    data = get_signin_status(email)
    response = requests.post(f"{form_url}/formResponse?emailAddress={email}")
    if response.status_code == 200:
        return f":white_check_mark: Sucessfully submitted form with email {email}, you are now signed {'out' if data else 'in'}."
    else:
        return f":x: Unknown error submitting form with email '{email}', http status: {response.status_code}"


@app.route("/commands/status", methods=["POST"])
def status():
    user = flask.request.values.get("user_id")
    email = user_data.get(user)
    if not email:
        return f":x: Please register your email with /sregister [email]"
    data = get_signin_status(email)
    if get_signin_status(email):
        return f":information_source: {data[0]} {data[1]} ({email}) has been in since {data[3]}"
    else:
        return f":information_source: {email} is currently signed out"


def get_signin_status(email):
    data = gsheets.get_range(sheet_id, sheet_range)[1:]  # account for headers
    for entry in data:
        if entry[2] == email:
            return entry
    return False
