from flask import Flask, abort, render_template, redirect, session, url_for, request, flash
import os
import requests
import json
from config import config
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError
from requests_oauthlib import OAuth2Session

app = Flask(__name__)

app.secret_key = config["app-secret"]

def get_guilds_config():
    result = {}
    for discord in config["discords"]:
        result[discord["guild_id"]] = discord
    return result

def json_or_text(response):
    text = response.text
    if response.headers['content-type'] == 'application/json':
        return response.json()
    return text

def discordapi_request(verb, url, **kwargs):
    headers = {
        'User-Agent': "University of Washington Discord Authentication",
        'Authorization': 'Bot {}'.format(config["bot-token"]),
    }
    params = None
    if 'params' in kwargs:
        params = kwargs['params']
    data = None
    if 'data' in kwargs:
        data = kwargs['data']
    if 'json' in kwargs and kwargs["json"] != False:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(data)
    url_formatted = "https://discordapp.com/api/v6" + url
    if data and "payload_json" in data:
        if "Content-Type" in headers:
            del headers["Content-Type"]
        req = requests.request(verb, url_formatted, params=params, files=data, headers=headers)
    else:
        req = requests.request(verb, url_formatted, params=params, data=data, headers=headers)
    return {
        'success': 300 > req.status_code >= 200,
        'content': json_or_text(req),
        'code': req.status_code,
    }

def discordapi_get_guild(guild_id):
    _endpoint = "/guilds/{guild_id}".format(guild_id=guild_id)
    r = discordapi_request("GET", _endpoint)
    return r

def discordapi_get_guild_member(guild_id, user_id):
    _endpoint = "/guilds/{guild_id}/members/{user_id}".format(guild_id=guild_id, user_id=user_id)
    r = discordapi_request("GET", _endpoint)
    return r

def discordapi_add_guild_member_role(guild_id, user_id, role_id):
    _endpoint = "/guilds/{guild_id}/members/{user_id}/roles/{role_id}".format(guild_id=guild_id, user_id=user_id, role_id=role_id)
    r = discordapi_request("PUT", _endpoint)
    return r

def discordapi_remove_guild_member_role(guild_id, user_id, role_id):
    _endpoint = "/guilds/{guild_id}/members/{user_id}/roles/{role_id}".format(guild_id=guild_id, user_id=user_id, role_id=role_id)
    r = discordapi_request("DELETE", _endpoint)
    return r

def discordapi_create_message(channel_id, content):
    _endpoint = "/channels/{channel_id}/messages".format(channel_id=channel_id)
    payload = {'content': content}
    r = discordapi_request("POST", _endpoint, data=payload)
    return r

def update_user_token(discord_token):
    session['discord_token'] = discord_token

def make_authenticated_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=config['client-id'],
        token=token,
        state=state,
        scope=scope,
        redirect_uri=url_for("callback", _external=True),
        auto_refresh_kwargs={
            'client_id': config['client-id'],
            'client_secret': config['client-secret'],
        },
        auto_refresh_url="https://discordapp.com/api/oauth2/token",
        token_updater=update_user_token,
    )

def discordapiuser_request(endpoint):
    token = session['discord_token']
    discord = make_authenticated_session(token=token)
    try:
        req = discord.get("https://discordapp.com/api/v6{}".format(endpoint))
    except InvalidGrantError as ex:
        abort(401)
    return req

def discordapiuser_get_current_authenticated_user():
    req = discordapiuser_request("/users/@me")
    if req.status_code != 200:
        abort(req.status_code)
    user = req.json()
    return user

@app.route("/")
def index():
    return "Welcome! This is a service to authenticate class Discords. Conceptualized during a UWB Independent Study by Jeremy Zhang. https://github.com/EndenDragon/uw-discord-auth<br>To access a server, please visit {} where SERVER_ID is the ID of your Discord server.".format(url_for("step1", guild_id="SERVER_ID", _external=True))

@app.route("/<guild_id>")
def step1(guild_id):
    guilds_config = get_guilds_config()
    if guild_id not in guilds_config:
        abort(404)
    guild = discordapi_get_guild(guild_id)
    if not guild["success"]:
        abort(404)
    guild = guild["content"]
    return render_template("layout.html", guild=guild, step=1)

@app.route("/<guild_id>/step2")
def step2(guild_id):
    guilds_config = get_guilds_config()
    if guild_id not in guilds_config:
        abort(404)
    guild = discordapi_get_guild(guild_id)
    if not guild["success"]:
        abort(404)
    guild = guild["content"]
    return render_template("layout.html", guild=guild, step=2)

@app.route('/callback', methods=["GET"])
def callback():
    state = session.get('oauth2_state')
    if not state:
        return redirect(url_for('logout', error="state_error"))
    if request.values.get('error'):
        return redirect(url_for('logout', error="discord_error {}".format(request.values.get('error'))))
    discord = make_authenticated_session(state=state)
    discord_token = discord.fetch_token(
        "https://discordapp.com/api/oauth2/token",
        client_secret=config['client-secret'],
        authorization_response=request.url)
    if not discord_token:
        return redirect(url_for('logout', error="discord_user_token_fetch_error"))
    session['discord_token'] = discord_token
    user = discordapiuser_get_current_authenticated_user()
    if session["redirect"]:
        redir = session["redirect"]
        session['redirect'] = None
        return redirect(redir)
    return redirect(url_for("index"))

@app.route("/login", methods=["GET"])
def login():
    session["redirect"] = request.args.get("redirect")
    scope = ['identify']
    discord = make_authenticated_session(scope=scope)
    authorization_url, state = discord.authorization_url(
        "https://discordapp.com/api/oauth2/authorize",
        access_type="offline"
    )
    session['oauth2_state'] = state
    return redirect(authorization_url)

@app.route('/logout', methods=["GET"])
def logout():
    redir = session.get("redirect", None)
    if not redir:
        redir = request.args.get("redirect", None)
    session.clear()
    if redir:
        session['redirect'] = redir
        return redirect(session['redirect'])
    return redirect(url_for("index"))

@app.route("/<guild_id>/step3")
def step3(guild_id):
    guilds_config = get_guilds_config()
    if guild_id not in guilds_config:
        abort(404)
    if "discord_token" not in session:
        return redirect(url_for("login", redirect=request.url))
    user = discordapiuser_get_current_authenticated_user()
    guild = discordapi_get_guild(guild_id)
    if not guild["success"]:
        abort(404)
    guild = guild["content"]
    member = discordapi_get_guild_member(guild["id"], user["id"])
    error = not member["success"]
    return render_template("layout.html", guild=guild, user=user, error=error, step=3)

@app.route("/<guild_id>/step3", methods=["POST"])
def step3_post(guild_id):
    guilds_config = get_guilds_config()
    if guild_id not in guilds_config:
        abort(404)
    guild_config = guilds_config[guild_id]
    if "discord_token" not in session:
        return redirect(url_for("login", redirect=request.url))
    user = discordapiuser_get_current_authenticated_user()
    guild = discordapi_get_guild(guild_id)
    if not guild["success"]:
        abort(404)
    guild = guild["content"]
    member = discordapi_get_guild_member(guild["id"], user["id"])
    if not member["success"]:
        abort(404)
    for role_id in guild_config["role_remove"]:
        discordapi_remove_guild_member_role(guild["id"], user["id"], role_id)
    for role_id in guild_config["role_add"]:
        discordapi_add_guild_member_role(guild["id"], user["id"], role_id)
    if guild_config.get("log_channel", None):
        discordapi_create_message(guild_config["log_channel"], "**{}#{}** (<@{}>) has authenticated with UWNetID **{}**.".format(user["username"], user["discriminator"], user["id"], request.remote_user))
    flash('Successfully authenticated your access to the Discord server! You may now close this page.', 'success')
    return redirect(url_for("step3", guild_id=guild_id))
