"""Defines the app's routes. Includes OAuth2 support for DocuSign"""

from flask import render_template, url_for, redirect, session, flash, request
from flask_oauthlib.client import OAuth
from datetime import datetime, timedelta
import requests
import uuid
from app import app, ds_config, eg001_embedded_signing

@app.route("/")
def index():
    return render_template("home.html", title="Home - Python Code Examples")


@app.route("/index")
def r_index():
    return redirect(url_for("index"))


@app.route("/ds/must_authenticate")
def ds_must_authenticate():
    return render_template("must_authenticate.html", title="Must authenticate")


@app.route("/eg001", methods=["GET", "POST"])
def eg001():
    if request.method == 'POST':

        return redirect(eg001_embedded_signing.controller(request.form), code=302)
    else:
        print('------ {0}'.format(request.form))
        return '''
            <html lang="en"><body><form action="{url}" method="post" role="form">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

            <label for="last_name">Last name: </label>
            <input type="text" id="last_name" name="last_name" value = "Doe"/>

            <label for="first_name">First name: </label>
            <input type="text" id="first_name" name="first_name" value = "John"/>

            <label for="middle_initial">MI: </label>
            <input type="text" id="middle_initial" name="middle_initial" value = "R"/>

            <br>

            <label for="gender">Gender: </label><br>
            <input type="radio" id="male" name="gender" value = "male" checked/>
            <label for="male">Male</label><br>
            <input type="radio" id="female" name="gender" value = "female"/>
            <label for="female">Female</label><br>


            <br><br>

            <label for="mailing_address">Street address: </label>
            <input type="text" id="mailing_address" name="mailing_address" value = "123 Fake Street"/>

            <br>

            <label for="city">City: </label>
            <input type="text" id="city" name="city" value = "City"/>

            <label for="state">State: </label>
            <input type="text" id="state" name="state" value = "CA"/>

            <br>

            <label for="zip">ZIP: </label>
            <input type="text" id="zip" name="zip" value = "11111"/>

            <label for="county">County: </label>
            <input type="text" id="county" name="county" value = "County"/>

            <br><br>

            <label for="home_tel">Home telephone #: </label>
            <input type="text" id="home_tel" name="home_tel" value = "(555) 555-5555"/>

            <label for="email">Email: </label>
            <input type="text" id="email" name="email" value = "fake@email.com"/>

            <br><br>

            <label for="dob">Date of birth: </label>
            <input type="text" id="dob" name="dob" value = "01/01/1950"/>

            <label for="ssn">Social security #: </label>
            <input type="text" id="ssn" name="ssn" value = "555-55-5555"/>

            <br><br>

            <label for="req_start_date">Requested Start Date: </label>
            <input type="text" id="req_start_date" name="req_start_date" value = "01/01/2020"/>

            <br><br>

            <label for="pref_lang">Preferred language: </label><br>
            <input type="radio" id="english" name="pref_lang" value = "english" checked/>
            <label for="english">English</label><br>
            <input type="radio" id="other" name="pref_lang" value = "other"/>
            <label for="other">Other</label>
            <input type="text" id="other_lang" name="other_lang"/>

            <br>


            <input type="submit" value="Sign the document!"
                style="width:13em;height:2em;background:#1f32bb;color:white;font:bold 1.5em arial;margin: 3em;"/>
            </form></body>
        '''.format(url=request.url)

@app.route("/ds_return")
def ds_return():
    event = request.args.get("event")
    state = request.args.get("state")
    envelope_id = request.args.get("envelopeId")
    return render_template("ds_return.html",
        title = "Return from DocuSign",
        event =  event,
        envelope_id = envelope_id,
        state = state
    )


################################################################################
#
# OAuth support for DocuSign
#


def ds_token_ok(buffer_min=60):
    """
    :param buffer_min: buffer time needed in minutes
    :return: true iff the user has an access token that will be good for another buffer min
    """

    ok = "ds_access_token" in session and "ds_expiration" in session
    ok = ok and (session["ds_expiration"] - timedelta(minutes=buffer_min)) > datetime.utcnow()
    return ok


base_uri_suffix = "/restapi"
oauth = OAuth(app)
request_token_params = {"scope": "signature",
                        "state": lambda: uuid.uuid4().hex.upper()}
if not ds_config.DS_CONFIG["allow_silent_authentication"]:
    request_token_params["prompt"] = "login"
docusign = oauth.remote_app(
    "docusign",
    consumer_key=ds_config.DS_CONFIG["ds_client_id"],
    consumer_secret=ds_config.DS_CONFIG["ds_client_secret"],
    access_token_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/token",
    authorize_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth",
    request_token_params=request_token_params,
    base_url=None,
    request_token_url=None,
    access_token_method="POST"
)


@app.route("/ds/login")
def ds_login():
    return docusign.authorize(callback=url_for("ds_callback", _external=True))


@app.route("/ds/logout")
def ds_logout():
    ds_logout_internal()
    flash("You have logged out from DocuSign.")
    return redirect(url_for("index"))


def ds_logout_internal():
    # remove the keys and their values from the session
    session.pop("ds_access_token", None)
    session.pop("ds_refresh_token", None)
    session.pop("ds_user_email", None)
    session.pop("ds_user_name", None)
    session.pop("ds_expiration", None)
    session.pop("ds_account_id", None)
    session.pop("ds_account_name", None)
    session.pop("ds_base_path", None)
    session.pop("envelope_id", None)
    session.pop("eg", None)
    session.pop("envelope_documents", None)
    session.pop("template_id", None)


@app.route("/ds/callback")
def ds_callback():
    """Called via a redirect from DocuSign authentication service """
    # Save the redirect eg if present
    redirect_url = session.pop("eg", None)
    # reset the session
    ds_logout_internal()

    resp = docusign.authorized_response()
    if resp is None or resp.get("access_token") is None:
        return "Access denied: reason=%s error=%s resp=%s" % (
            request.args["error"],
            request.args["error_description"],
            resp
        )
    # app.logger.info("Authenticated with DocuSign.")
    flash("You have authenticated with DocuSign.")
    session["ds_access_token"] = resp["access_token"]
    session["ds_refresh_token"] = resp["refresh_token"]
    session["ds_expiration"] = datetime.utcnow() + timedelta(seconds=resp["expires_in"])

    # Determine user, account_id, base_url by calling OAuth::getUserInfo
    # See https://developers.docusign.com/esign-rest-api/guides/authentication/user-info-endpoints
    url = ds_config.DS_CONFIG["authorization_server"] + "/oauth/userinfo"
    auth = {"Authorization": "Bearer " + session["ds_access_token"]}
    response = requests.get(url, headers=auth).json()
    session["ds_user_name"] = response["name"]
    session["ds_user_email"] = response["email"]
    accounts = response["accounts"]
    account = None # the account we want to use
    # Find the account...
    target_account_id = ds_config.DS_CONFIG["target_account_id"]
    if target_account_id:
        account = next( (a for a in accounts if a["account_id"] == target_account_id), None)
        if not account:
            # Panic! The user does not have the targeted account. They should not log in!
            raise Exception("No access to target account")
    else: # get the default account
        account = next((a for a in accounts if a["is_default"]), None)
        if not account:
            # Panic! Every user should always have a default account
            raise Exception("No default account")

    # Save the account information
    session["ds_account_id"] = account["account_id"]
    session["ds_account_name"] = account["account_name"]
    session["ds_base_path"] = account["base_uri"] + base_uri_suffix

    if not redirect_url:
        redirect_url = url_for("index")
    return redirect(redirect_url)

################################################################################

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500
