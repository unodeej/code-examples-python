"""015: Get an envelope"s tab information data"""

import json
from os import path

from docusign_esign.client.api_exception import ApiException
from flask import render_template, session, Blueprint

from .controller import Eg015Controller
from ...docusign import authenticate
from ...ds_config import DS_CONFIG
from ...error_handlers import process_error

eg = "eg015"  # Reference (and URL) for this example
eg015 = Blueprint("eg015", __name__)


@eg015.route("/eg015", methods=["POST"])
@authenticate(eg=eg)
def envelope_tab_data():
    """
    1. Check presence of envelope_id in session
    2. Get required arguments
    3. Call the worker method
    4. Show Envelope tab data results
    """

    # 1. Check presence of envelope_id in session
    if "envelope_id" in session:

        # 2. Get required arguments
        args = Eg015Controller.get_args()

        try:
            # 3. Call the worker method
            results = Eg015Controller.worker(args)
        except ApiException as err:
            return process_error(err)

        # 4.Show Envelope tab data results
        return render_template(
            "example_done.html",
            title="Get envelope tab data results",
            h1="Get envelope tab data results",
            message="Results from the Envelopes::formData GET method:",
            json=json.dumps(json.dumps(results.to_dict()))
        )

    else:
        return render_template(
            "eg015_envelope_tab_data.html",
            title="Envelope Tab Data",
            envelope_ok=False,
            source_file=path.basename(path.dirname(__file__)) + "/controller.py",
            source_url=DS_CONFIG["github_example_url"] + path.basename(path.dirname(__file__)) + "/controller.py",
            documentation=DS_CONFIG["documentation"] + eg,
            show_doc=DS_CONFIG["documentation"],
        )


@eg015.route("/eg015", methods=["GET"])
@authenticate(eg=eg)
def get_view():
    """responds with the form for the example"""

    return render_template(
        "eg015_envelope_tab_data.html",
        title="Envelope information",
        envelope_ok="envelope_id" in session,
        source_file=path.basename(path.dirname(__file__)) + "/controller.py",
        source_url=DS_CONFIG["github_example_url"] + path.basename(path.dirname(__file__)) + "/controller.py",
        documentation=DS_CONFIG["documentation"] + eg,
        show_doc=DS_CONFIG["documentation"],
    )
