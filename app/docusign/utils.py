from datetime import timedelta, datetime
from functools import wraps

from docusign_esign import ApiClient
from flask import session, flash, url_for, redirect

from .ds_client import DSClient
from ..consts import minimum_buffer_min


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
    session.pop("auth_type", None)
    DSClient.destroy()


def create_api_client(base_path, access_token):
    """Create api client and construct API headers"""
    api_client = ApiClient()
    api_client.host = base_path
    api_client.set_default_header(header_name="Authorization", header_value=f"Bearer {access_token}")

    return api_client


def ds_token_ok(buffer_min=60):
    """
    :param buffer_min: buffer time needed in minutes
    :return: true iff the user has an access token that will be good for another buffer min
    """

    ok = "ds_access_token" in session and "ds_expiration" in session
    ok = ok and (session["ds_expiration"] - timedelta(minutes=buffer_min)) > datetime.utcnow()

    return ok


def authenticate(eg):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if ds_token_ok(minimum_buffer_min):
                return func(*args, **kwargs)
            else:
                # We could store the parameters of the requested operation
                # so it could be restarted automatically.
                # But since it should be rare to have a token issue here,
                # we"ll make the user re-enter the form data after
                # authentication.
                session["eg"] = url_for(eg + ".get_view")
                if session.get("auth_type"):
                    flash("Token has been updated")
                    return redirect(url_for("ds.ds_login"))
                else:
                    return redirect(url_for("ds.ds_must_authenticate"))

        return wrapper

    return decorator
