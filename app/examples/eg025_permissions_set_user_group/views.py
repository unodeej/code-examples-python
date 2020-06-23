"""Example 025: Set a permission profile for a group of users"""

from os import path
from docusign_esign.client.api_exception import ApiException
from flask import current_app as app
from flask import render_template, session, request, Blueprint
from .controller import Eg025Controller
from ...docusign import authenticate
from ...ds_config import DS_CONFIG
from ...error_handlers import process_error

eg = "eg025"
eg025 = Blueprint("eg025", __name__)

@eg025.route("/eg025", methods=["POST"])
@authenticate(eg=eg)
def permissions_set_user_group():
    """
    1. Get required arguments
    2. Call the worker method
    3. Render a response
    """

    # 1. Get required arguments
    args = Eg025Controller.get_args()
    try:
        # 2. Call the worker method to set the permission profile
        response = Eg025Controller.worker(args)
        app.logger.info(f"The permission profile has been set.")
        permission_profile_id = response.groups[0].permission_profile_id
        group_id = response.groups[0].group_id

        # 3. Render the response
        return render_template(
            "example_done.html",
            title="Set a permission profile for a group of users",
            h1="Setting a permission profile for a group of users",
            message=f"""The permission profile has been set!<br/>"""
                    f"""Permission profile ID: {permission_profile_id}<br/>"""
                    f"""Group id: {group_id}"""
        )

    except ApiException as err:
        return process_error(err)

@eg025.route("/eg025", methods=["GET"])
@authenticate(eg=eg)
def get_view():
    """Responds with the form for the example"""

    args = {
        "account_id": session["ds_account_id"],  # Represents your {ACCOUNT_ID}
        "base_path": session["ds_base_path"],
        "access_token": session["ds_access_token"],  # Represents your {ACCESS_TOKEN}
    }
    permission_profiles, groups = Eg025Controller.get_data(args)
    return render_template(
        "eg025_permissions_set_user_group.html",
        title="Setting a permission profile",
        source_file=path.basename(path.dirname(__file__)) + "/controller.py",
        source_url=DS_CONFIG["github_example_url"] + path.basename(path.dirname(__file__)) + "/controller.py",
        documentation=DS_CONFIG["documentation"] + eg,
        show_doc=DS_CONFIG["documentation"],
        permission_profiles=permission_profiles,
        groups=groups
    )