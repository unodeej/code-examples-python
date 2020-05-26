"""Defines the app's routes. Includes OAuth2 support for DocuSign"""

from flask import render_template, url_for, redirect, session, flash, request, render_template
#from flask_oauthlib.client import OAuth
#from flask.json import jsonify
from authlib.integrations.flask_client import OAuth, token_update

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired
from app.forms import ClientForm

from datetime import datetime, timedelta
import requests
#from requests_oauthlib import OAuth2Session
import uuid
from app import app, ds_config, eg001_embedded_signing
from time import time
import pickle
import os.path
from os import path

# number of (seconds?) that token lasts for
TOKEN_LIFETIME = 24000

class MyForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()])

record = {'field1': 'label1',
          'field2': 'label2'
         }
for key, value in record.items():
    setattr(MyForm, key, StringField(value))

class OAuth2Token():
    access_token = ""
    refresh_token = ""
    expires_at = ""
    def save(self, token):
        print("saving")
        write_token_to_file(token)

@app.route("/")
def index():
    # ds_logout_internal()
    # print('back')
    return render_template("home.html", title="Home - Python Code Examples")


@app.route("/index")
def r_index():
    return redirect(url_for("index"))


@app.route("/ds/must_authenticate")
def ds_must_authenticate():
    return ds_login()
    #return render_template("auto_auth.html", title="Must authenticate")

    #return render_template("must_authenticate.html", title="Must authenticate")


@app.route("/eg001", methods=["GET", "POST"])
def eg001():
    print("eg001!")
    # This needs to be executed here, so that the auth process can be carried out
    return eg001_embedded_signing.controller()
    # if request.method == 'POST':
    #     return #redirect(eg001_embedded_signing.controller(request.form), code=302)
    # else:
    #     form = ClientForm()
    #
    #     if form.validate() == False:
    #         flash:('All fields are required.')
    #     return render_template('form.html', form = form)

@app.route('/submit', methods=('GET', 'POST'))
def submit():
    form = MyForm()
    if form.validate_on_submit():
        print("form submission successful!")
        return redirect('/success')
    return render_template('submit.html', form=form)

@app.route('/success',methods = ['GET','POST'])
def success():
    print("success route!")
    return eg001_embedded_signing.create_controller()

if __name__ == '__main__':
   app.run(debug = True)



@app.route("/ds_return")
def ds_return():
    event = request.args.get("event")
    state = request.args.get("state")
    envelope_id = request.args.get("envelopeId")
    return render_template("ds_return.html",
        title =  "Return from DocuSign",
        event =  event,
        envelope_id = envelope_id,
        state =  state
    )

@app.route("/download_doc")
def download_doc():
    return eg001_embedded_signing.download_doc()


################################################################################
#
# OAuth support for DocuSign
#
# @token_update.connect_via(app)
# def on_token_update(sender, name, token, refresh_token=None, access_token=None):
#     print("~~BLINKER: AUTO TOKEN UPDATE!~~")
#     item = OAuth2Token()
#
#     # update old token
#     item.access_token = token['access_token']
#     item.refresh_token = token.get('refresh_token')
#     item.expires_at = token['expires_at']
#     item.save(token)

# # This function is passed into the app so that it automatically refreshes the token
def update_token(name, token, refresh_token=None, access_token=None):
    print("~~AUTO UPDATING TOKEN~~")
    # if refresh_token:
    #     item = OAuth2Token.find(name=name, refresh_token=refresh_token)
    # elif access_token:
    #     item = OAuth2Token.find(name=name, access_token=access_token)
    # else:
    #     return
    write_token_to_file(token)

    item = OAuth2Token()

    print("TOKEN SAYS")
    print(token)
    # update old token
    item.access_token = token['access_token']
    item.refresh_token = token.get('refresh_token')
    item.expires_at = token['expires_at']
    item.save(token)



def ds_token_ok(buffer_min=60):
    """
    :param buffer_min: buffer time needed in minutes
    :return: true iff the user has an access token that will be good for another buffer min
    """
    # buffer_min = 0
    ok = "ds_access_token" in session and "ds_expiration" in session

    # print(session["ds_expiration"])
    ok = ok and (session["ds_expiration"] - timedelta(minutes=buffer_min)) > datetime.utcnow()
    print("Is token ok? " + str(ok))
    return ok






base_uri_suffix = "/restapi"

# Register the docusign OAuth remote app
oauth = OAuth(app, update_token=update_token)

oauth.register(
    name='docusign',
    client_id=ds_config.DS_CONFIG["ds_client_id"],
    client_secret=ds_config.DS_CONFIG["ds_client_secret"],
    access_token_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/token",
    access_token_params=None,
    authorize_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth",
    authorize_params=None,
    api_base_url=None,
    client_kwargs={
        'scope': 'signature',
        'refresh_token_url': ds_config.DS_CONFIG["authorization_server"] + "/oauth/token"
        # "state": lambda: uuid.uuid4().hex.upper(),
        # 'code': "abcdef"
        },
    )

# Create the remote app
docusign = oauth.docusign
# request_token_params = {"scope": "signature",
#                         "state": lambda: uuid.uuid4().hex.upper()}
# if not ds_config.DS_CONFIG["allow_silent_authentication"]:
#     request_token_params["prompt"] = "login"
#
# docusign = oauth.remote_app(
#     "docusign",
#     consumer_key=ds_config.DS_CONFIG["ds_client_id"],
#     consumer_secret=ds_config.DS_CONFIG["ds_client_secret"],
#     access_token_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/token",
#     authorize_url=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth",
#     request_token_params=request_token_params,
#     base_url=None,
#     request_token_url=None,
#     access_token_method="POST"
# )


@app.route("/ds/login")
def ds_login():
    print("LOGIN PROCESS")



    # if the access token and expiry are present, it means we've logged in once before
    if "ds_access_token" in session and "ds_expiration" in session:
        # if we have a valid access token that hasn't expired, just log in
        if ds_token_ok():
            print("Auto log in using un-expired access token")
            return docusign.authorize_redirect(url_for("ds_callback", _external=True) )
            #return docusign.authorize(callback=url_for("ds_callback", _external=True))

        # if we have a valid ACCESS token, but it has expired, use the REFRESH token to generate a new access token
        else:
            print("CAN REFRESH!!! (token is expired, but we can auto-refresh it)")

            return redirect(url_for("ds_callback", _external=True) )

            # token = docusign.refresh_token( ds_config.DS_CONFIG["authorization_server"] + "/oauth/token", session["ds_refresh_token"] )
            # #
            # give_token_to_sesssion(token)

            # url = ds_config.DS_CONFIG["authorization_server"] + "/oauth/userinfo"
            #
            # auth = {"Authorization": "Bearer " + session["ds_access_token"]}
            #
            # response = docusign.get(url, headers=auth).json()



            #return redirect(url_for("eg001", _external=True))
            #return docusign.authorize_redirect(url_for("ds_callback", _external=True) )

            # returns an OAuthResponse object
            # Parameters:
            # url – where to send the request to
            # data – the data to be sent to the server. If the request method is GET the data is appended to the URL as query parameters, otherwise encoded to format if the format is given. If a content_type is provided instead, the data must be a string encoded for the given content type and used as request body.
            # headers – an optional dictionary of headers.
            # format – the format for the data. Can be urlencoded for URL encoded data or json for JSON.
            # method – the HTTP request method to use.
            # content_type – an optional content type. If a content type is provided, the data is passed as it and the format parameter is ignored.
            # token – an optional token to pass to tokengetter. Use this if you want to support sending requests using multiple tokens. If you set this to anything not None, tokengetter_func will receive the given token as an argument, in which case the tokengetter should return the (token, secret) tuple for the given token.
            # response = docusign.request(
            #     ds_config.DS_CONFIG["authorization_server"] + "/oauth/token",
            #     None,
            #     [],
            #     "urlencoded",
            #     'POST',
            #     "refresh_token",
            #     session["ds_refresh_token"]
            #
            # );
            #
            # print("RESPONSE")
            # print(response)
            # print(response.data)
            # print(response.raw_data)
            # print(response.status)

            # google = OAuth2Session(ds_config.DS_CONFIG["ds_client_id"], redirect_uri=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth")
            #
            # DOCU = OAuth2Session(ds_config.DS_CONFIG["ds_client_id"], redirect_uri=ds_config.DS_CONFIG["authorization_server"] + "/oauth/auth",
            #                         state = google.authorization_url(ds_config.DS_CONFIG["authorization_server"], access_type="offline", prompt="select_account"))

            # DOCU = oauth.remote_app(
            #     "docusign",
            #     grant_type= 'refresh_token',
            #     access_token_params= {
            #     session['ds_refresh_token']
            #     }
            # )
            #
            # token = DOCU.fetch_token(ds_config.DS_CONFIG["authorization_server"] + "/oauth/token", client_secret=ds_config.DS_CONFIG["ds_client_secret"],
            #                    authorization_response=request.url)
            #
            # # Generate an access token and store it in session["ds_access_token"]
            # # token = session["ds_access_token"]
            #
            # extra = {
            #     'client_id': ds_config.DS_CONFIG["ds_client_id"],
            #     'client_secret': ds_config.DS_CONFIG["ds_client_secret"]
            # }
            #
            # ds = OAuth2Session(ds_config.DS_CONFIG["ds_client_id"],
            #                    token=token)
            #
            #
            #
            # session["ds_access_token"] = ds.refresh_token(ds_config.DS_CONFIG["authorization_server"] + "/oauth/token", **extra)
            # return jsonify(session['oauth_token'])

    # if the access token isn't present, it means we've never logged in before
    else:
        # perform first-time login
        print("First Time Login! (session is empty, autogenerating token from file)")

        return redirect(url_for("ds_callback", _external=True))
        #return docusign.authorize_redirect(url_for("ds_callback", _external=True) )



# Called when we press the log out button at the top of the page
@app.route("/ds/logout")
def ds_logout():
    ds_logout_internal()
    flash("You have logged out from DocuSign.")
    return redirect(url_for("index"))


def ds_logout_internal():
    print("DS_LOGOUT")
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

def write_token_to_file(token):
    # Just for testing
    # token["expires_in"] = TOKEN_LIFETIME
    # token["expires_at"] = time() + token["expires_in"]
    print("WRITE TOKEN TO FILE")

    # Write the new token to file
    with open('stored_token', 'wb') as stored_token_file:
        pickle.dump(token, stored_token_file)


@app.route("/ds/callback")
def ds_callback():
    """Called via a redirect from DocuSign authentication service """
    print("Callback")

    # Save the redirect eg if present
    redirect_url = session.pop("eg", None)

    # Load the token from one we have stored in file
    if path.isfile('stored_token'):
        # Load the stored token from
        print("LOADING STORED TOKEN FILE")
        with open('stored_token', 'rb') as stored_token_file:
            token = pickle.load(stored_token_file)
    else:
        print("ERROR: file 'stored_token' not found. Redirecting to authentication to generate a new one.")
        #Get the access token, refresh token, and expiration, via inputting login credentials
        # if ds_token_ok():
        #     token = docusign.token
        # else:

        #return docusign.authorize_redirect(url_for("ds_callback", _external=True) )
        token = oauth.docusign.authorize_access_token()   # For some reason this doesn't work

        write_token_to_file(token)

    # CRUCIAL!!! This step lets the remote_app know that we have a new token
    docusign.token = token

    # Clear the session, and fill in the new session vars
    ds_logout_internal()
    give_token_to_sesssion(token)


    # if "ds_refresh_token" in session:
    #     print("LOADING STORED TOKEN FILE")
    #     with open('stored_token', 'rb') as stored_token_file:
    #         token = pickle.load(stored_token_file)
    #
    #     docusign.token = token
    #
    #     #oauth.update_token("docusign", token)
    #     ds_logout_internal()
    #     give_token_to_sesssion(token)
    #
    #     # url = ds_config.DS_CONFIG["authorization_server"] + "/oauth/userinfo"
    #     #
    #     # auth = {"Authorization": "Bearer " + session["ds_access_token"]}
    #     #
    #     # response = docusign.get(url, headers=auth).json()
    #
    # else:
    #     # reset the session
    #     ds_logout_internal()
    #
    #
    #     # Get the access token, refresh token, and expiration
    #     token = oauth.docusign.authorize_access_token()
    #
    #     with open('stored_token', 'wb') as stored_token_file:
    #         pickle.dump(token, stored_token_file)
    #
    #     give_token_to_sesssion(token)


    # Redirect to the form page
    if not redirect_url:
        redirect_url = url_for("index")
    return redirect(url_for("eg001"))

    # resp = docusign.authorized_response()
    # if resp is None or resp.get("access_token") is None:
    #     return "Access denied: reason=%s error=%s resp=%s" % (
    #         request.args["error"],
    #         request.args["error_description"],
    #         resp
    #     )
    # # app.logger.info("Authenticated with DocuSign.")
    # flash("You have authenticated with DocuSign.")
    # session["ds_access_token"] = resp["access_token"]
    # session["ds_refresh_token"] = resp["refresh_token"]
    # session["ds_expiration"] = datetime.utcnow() + timedelta(seconds=resp["expires_in"])


# Pass in a token to the session, and fill in all the session values with info from the token
# Also gets user info from the remote app (name, email, etc.) and passes it to the session
def give_token_to_sesssion(token):
    print("give_token_to_sesssion(): TOKEN:")
    print(token)
    # print(datetime.utcnow())

    # token['expires_in'] = TOKEN_LIFETIME

    session["ds_access_token"] = token['access_token']
    session["ds_refresh_token"] = token['refresh_token']
    session["ds_expiration"] = datetime.utcnow() + timedelta(seconds=token['expires_in'])

    print("Expiration Date:")
    print(session['ds_expiration'])

    # Get the user info
    url = ds_config.DS_CONFIG["authorization_server"] + "/oauth/userinfo"

    auth = {"Authorization": "Bearer " + session["ds_access_token"]}

    # This GET request should automatically update the token if it's expired
    response = docusign.get(url, headers=auth).json()

    # print("RESPONSE")
    # print(response)

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

################################################################################

@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500
