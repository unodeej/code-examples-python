"""007: Get an envelope"s document"""

from os import path

from docusign_esign.client.api_exception import ApiException
from flask import render_template, session, send_file, Blueprint

from .controller import Eg007Controller
from ...docusign import authenticate
from ...ds_config import DS_CONFIG
from ...error_handlers import process_error

eg = "eg007"  # reference (and url) for this example
eg007 = Blueprint("eg007", __name__)


@eg007.route("/eg007", methods=["POST"])
@authenticate(eg=eg)
def get_envelope_doc():
    """
    1. Get required arguments
    2. Call the worker method
    3. Download envelope document
    """

    if "envelope_id" in session and "envelope_documents" in session:
        # 1. Get required arguments
        args = Eg007Controller.get_args()
        try:
            # 2. Call the worker method
            results = Eg007Controller.worker(args)
        except ApiException as err:
            return process_error(err)

        # 3. Download envelope document
        return send_file(
            results["data"],
            mimetype=results["mimetype"],
            as_attachment=True,
            attachment_filename=results["doc_name"]
        )
    else:
        return render_template(
            "eg007_envelope_get_doc.html",
            title="Download an Envelope's Document",
            envelope_ok=False,
            documents_ok=False,
            source_file=path.basename(path.dirname(__file__)) + "/controller.py",
            source_url=DS_CONFIG["github_example_url"] + path.basename(path.dirname(__file__)) + "/controller.py",
            documentation=DS_CONFIG["documentation"] + eg,
            show_doc=DS_CONFIG["documentation"],
        )


@eg007.route("/eg007", methods=["GET"])
@authenticate(eg=eg)
def get_view():
    """responds with the form for the example"""

    documents_ok = "envelope_documents" in session
    document_options = []
    if documents_ok:
        # Prepare the select items
        envelope_documents = session["envelope_documents"]
        document_options = map(lambda item:
                               {"text": item["name"], "document_id": item["document_id"]}
                               , envelope_documents["documents"])

    return render_template(
        "eg007_envelope_get_doc.html",
        title="Download an Envelope's Document",
        envelope_ok="envelope_id" in session,
        documents_ok=documents_ok,
        source_file=path.basename(path.dirname(__file__)) + "/controller.py",
        source_url=DS_CONFIG["github_example_url"] + path.basename(path.dirname(__file__)) + "/controller.py",
        documentation=DS_CONFIG["documentation"] + eg,
        show_doc=DS_CONFIG["documentation"],
        document_options=document_options
    )
