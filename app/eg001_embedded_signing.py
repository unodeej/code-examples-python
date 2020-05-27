"""Example 001: Embedded Signing Ceremony"""

from flask import render_template, url_for, redirect, session, flash, request, send_file, make_response
from os import path
import json
from app import app, ds_config, views
from app.forms import ClientForm
import base64
import re
from docusign_esign import *
from docusign_esign.client.api_exception import ApiException
import csv
import io

eg = "eg001"  # reference (and url) for this example
signer_client_id = 1000 # Used to indicate that the signer will use an embedded
                        # Signing Ceremony. Represents the signer's userId within
                        # your application.
authentication_method = "None" # How is this application authenticating
                               # the signer? See the 'authenticationMethod' definition
                               # https://developers.docusign.com/esign-rest-api/reference/Envelopes/EnvelopeViews/createRecipient

demo_docs_path = path.abspath(path.join(path.dirname(path.realpath(__file__)), "static/demo_documents"))

class FormEntry():
    value = ""

    def __init__(self, type, name, anchor):
        self.type = type
        self.name = name
        self.anchor = anchor

def download_doc():
    """
    1. Call the envelope get method
    """
    # import pdb; pdb.set_trace()
    args = {
        "account_id": session["ds_account_id"],
        "document_id": 1,
        "envelope_id": session["envelope_id"],
        "envelope_documents": session["envelope_documents"],
        "base_path": session["ds_base_path"],
        "ds_access_token": session["ds_access_token"]
    }

    # Exceptions will be caught by the calling function
    api_client = ApiClient()
    api_client.host = args['base_path']
    api_client.set_default_header("Authorization", "Bearer " + args['ds_access_token'])
    envelope_api = EnvelopesApi(api_client)
    document_id = args['document_id']

    # The SDK always stores the received file as a temp file
    temp_file = envelope_api.get_document(args['account_id'], document_id, args['envelope_id'])
    print(args['envelope_documents']['documents'])
    doc_item = next(item for item in args['envelope_documents']['documents'] if item['document_id'] == document_id)
    doc_name = doc_item['name']
    has_pdf_suffix = doc_name[-4:].upper() == '.PDF'
    pdf_file = has_pdf_suffix
    # Add .pdf if it's a content or summary doc and doesn't already end in .pdf
    if (doc_item["type"] == "content" or doc_item["type"] == "summary") and not has_pdf_suffix:
        doc_name += ".pdf"
        pdf_file = True
    # Add .zip as appropriate
    if doc_item["type"] == "zip":
        doc_name += ".zip"

    # Return the file information
    if pdf_file:
        mimetype = 'application/pdf'
    elif doc_item["type"] == 'zip':
        mimetype = 'application/zip'
    else:
        mimetype = 'application/octet-stream'

    # {'mimetype': mimetype, 'doc_name': doc_name, 'data': temp_file}

    return send_file(temp_file, attachment_filename=doc_name)

def download_csv():
    print("DOWNLOAD CSV")
    print(session)

    # whatever we want to call the new file
    file_name = 'data.csv'

    with open(file_name, mode='w') as csv_file:
        si = io.StringIO()
        writer = csv.writer(si) #csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for d in session["csv_data"]:
            writer.writerow(d)

        output = make_response(si.getvalue())

        output.headers["Content-Disposition"] = "attachment; filename=" + file_name
        output.headers["Content-type"] = "text/csv"
        return output

def controller():
    """Controller router using the HTTP method"""
    if request.method == "GET":
        return get_controller()
    # elif request.method == "POST":
    #     form = ClientForm()
    #
    #     if form.validate() == False:
    #         flash:('All fields are required.')
    #     return render_template('form.html', form = form)
    else:
        return render_template("404.html"), 404


def create_controller():
    """
    1. Check the token
    2. Call the worker method
    3. Redirect the user to the signing ceremony
    """

    # print("FORM DATA: " + str(request.form))

    # Names of the variables from forms.py
    form_variable_names = [
        FormEntry("select", "pdf_aarp", "eh_pdf_name"),
        FormEntry("select", "pdf_aetna", "eh_pdf_name"),
        FormEntry("select", "pdf_alignment", "eh_pdf_name"),
        FormEntry("select", "pdf_anthem", "eh_pdf_name"),

        FormEntry("radio", "title", "eh_title"),
        FormEntry("text", "first_name", "eh_first_name"),
        FormEntry("text", "middle_initial", "eh_middle_initial"),
        FormEntry("text", "last_name", "eh_last_name"),
        FormEntry("text", "home_address", "eh_home_address"),
        FormEntry("text", "city", "eh_city"),
        FormEntry("text", "state", "eh_state"),
        FormEntry("text", "zip", "eh_zip"),
        FormEntry("bool", "diff_mail_addr", "eh_diff_mail_addr"),
        FormEntry("text", "mailing_address", "eh_mailing_address"),
        FormEntry("text", "mailing_city", "eh_mailing_city"),
        FormEntry("text", "mailing_state", "eh_mailing_state"),
        FormEntry("text", "mailing_zip", "eh_mailing_zip"),
        FormEntry("text", "home_tel", "eh_home_tel"),
        FormEntry("text", "email", "eh_email"),
        FormEntry("text", "dob", "eh_dob"),
        FormEntry("text", "aarp", "eh_aarp"),
        FormEntry("select_mult", "add_coverage", "eh_add_coverage"),
        FormEntry("text", "claim_num", "eh_claim_num"),
        FormEntry("select", "hospital_month", "eh_hospital_month"),
        FormEntry("select", "hospital_year", "eh_hospital_year"),
        FormEntry("select", "medical_month", "eh_medical_month"),
        FormEntry("select", "medical_year", "eh_medical_year"),
        FormEntry("select", "plan_type", "eh_plan_type"),
        FormEntry("text", "ins_company", "eh_ins_company"),
        FormEntry("text", "policy_id", "eh_policy_id"),
        FormEntry("text", "ins_start_date", "eh_ins_start_date"),
        FormEntry("text", "ins_end_date", "eh_ins_end_date"),
        FormEntry("select", "pref_payment", "eh_pref_payment"),
        FormEntry("text", "bank_name", "eh_bank_name"),
        FormEntry("text", "account_number", "eh_account_number"),
        FormEntry("text", "routing_number", "eh_routing_number")
    ]


    minimum_buffer_min = 3     # four hours
    # Check the access token
    if views.ds_token_ok(minimum_buffer_min):
        # 2. Call the worker method
        # More data validation would be a good idea here
        # Strip anything other than characters listed
        pattern = re.compile("([^\w \-\@\.\,])+")

        envelope_args = {
            "signer_client_id": signer_client_id,
            "form_data": [],

            "ds_return_url": url_for("ds_return", _external=True)
        }

        # Populate envelope_args with the data from the form
        for v in form_variable_names:
            # print("name")
            # print(v.name)
            try:
                if "pdf_" in v.name:
                    v.value = request.form.get(v.name)
                else:
                    v.value = pattern.sub("", request.form.get(v.name))
            except:
                # If field is left blank, pass in empty string as value
                v.value = ""
            envelope_args["form_data"].append(v)

        # These args are used by Docusign for the electronic signature
        envelope_args["signer_email"] = request.form.get("email")
        envelope_args["signer_name"]  = request.form.get("first_name") + " " + request.form.get("last_name")

        # Pass args into worker
        args = {
            "account_id": session["ds_account_id"],
            "base_path": session["ds_base_path"],
            "ds_access_token": session["ds_access_token"],
            "envelope_args": envelope_args
        }

        try:
            results = worker(args)
        except ApiException as err:
            views.ds_logout();
            views.ds_login();
            return create_controller();
            # error_body_json = err and hasattr(err, "body") and err.body
            # # we can pull the DocuSign error code and message from the response body
            # error_body = json.loads(error_body_json)
            # error_code = error_body and "errorCode" in error_body and error_body["errorCode"]
            # error_message = error_body and "message" in error_body and error_body["message"]
            # # In production, may want to provide customized error messages and
            # # remediation advice to the user.
            #
            # return render_template("error.html",
            #                        err=err,
            #                        error_code=error_code,
            #                        error_message=error_message
            #                        )
        if results:
            # Redirect the user to the Signing Ceremony
            # Don"t use an iFrame!
            # State can be stored/recovered using the framework's session or a
            # query parameter on the returnUrl (see the makeRecipientViewRequest method)
            print("SIGNING CEREMONY")
            # print(results["redirect_url"])

            session["envelope_id"] = results["envelope_id"]

            return redirect(results["redirect_url"])

    else:
        print("must_authenticate")
        flash("Sorry, you need to re-authenticate.")
        # We could store the parameters of the requested operation
        # so it could be restarted automatically.
        # But since it should be rare to have a token issue here,
        # we'll make the user re-enter the form data after
        # authentication.
        session["eg"] = url_for(eg)
        return redirect(url_for("ds_must_authenticate"))


# ***DS.snippet.0.start
def worker(args):
    """
    1. Create the envelope request object
    2. Send the envelope
    3. Create the Recipient View request object
    4. Obtain the recipient_view_url for the signing ceremony
    """
    # COMPOSITE TEMPLATES, FOR PDF FORM FILL
    # api_client = create_api_client(base_path=args["base_path"], access_token=args["ds_access_token"])
    # # CREATE COMPOSITE TEMPLATE
    # templates_api = TemplatesApi(api_client)
    #
    # template_name = ""
    # templates_results = templates_api.list_templates(account_id=args["account_id"], search_text=template_name)
    # created_new_template = False
    # if int(templates_results.result_set_size) > 0:
    #     template_id = templates_results.envelope_templates[0].template_id
    #     results_template_name = templates_results.envelope_templates[0].name
    # else:
    #
    #     # Template not found -- so create it
    #     # 2. create the template
    #     template_req_object = make_template_req()
    #     res = templates_api.create_template(account_id=args["account_id"], envelope_template=template_req_object)
    #     # Pick the first template object within the result
    #     templates_results = res.templates[0]
    #     template_id = templates_results.template_id
    #     results_template_name = templates_results.name
    #     created_new_template = True

    envelope_args = args["envelope_args"]

    # envelope_args["template_id"] = template_id
    # envelope_args["template_name"] = results_template_name
    # envelope_args["created_new_template"] = created_new_template

    # 1. Create the envelope request object
    envelope_definition = make_envelope(envelope_args)


    # 2. call Envelopes::create API method
    # Exceptions will be caught by the calling function
    api_client = ApiClient()
    api_client.host = args["base_path"]
    api_client.set_default_header("Authorization", "Bearer " + args["ds_access_token"])

    envelope_api = EnvelopesApi(api_client)
    results = envelope_api.create_envelope(args["account_id"], envelope_definition=envelope_definition)

    # print("RESULTS!")
    # print(results)

    envelope_id = results.envelope_id
    app.logger.info(f"Envelope was created. EnvelopeId {envelope_id}")


    # STORE ENVELOPE ARGS IN SESSION! This may be insecure; don't leave confidential client data exposed!
    print("ENV ARGS")
    print(envelope_args['form_data'])
    csv_data = []
    for f in envelope_args['form_data']:
        csv_data.append( [f.name, f.value] )
    session["csv_data"] = csv_data

    # 3. Create the Recipient View request object
    recipient_view_request = RecipientViewRequest(
        authentication_method = authentication_method,
        client_user_id = envelope_args["signer_client_id"],
        recipient_id = "1",
        return_url = envelope_args["ds_return_url"],
        user_name = envelope_args["signer_name"], email = envelope_args["signer_email"]
    )
    # 4. Obtain the recipient_view_url for the signing ceremony
    # Exceptions will be caught by the calling function
    results = envelope_api.create_recipient_view(args["account_id"], envelope_id,
        recipient_view_request = recipient_view_request)


    # print("ENVELOPE DEFINITION")
    # print(envelope_definition.documents)

    # print ("MYURL" + results.url)
    return {"envelope_id": envelope_id, "redirect_url": results.url}


# Author: DJ Uno
# This function sets up the signature and text field tabs for the document.
def setup_tabs(existingTabs, args):
    # Create Text tabs
    text_fields = []
    isMale = False
    isEnglish = False

    for a in args:
        if a.type == "text":
            text_fields.append(
                Text( # DocuSign SignHere field/tab
                    document_id = '1', page_number = '1',
                    anchor_string = a.anchor, anchor_x_offset = 0, anchor_y_offset = 0, anchor_units = "inches",
                    # anchor_case_sensitive = True,
                    font = "helvetica", font_size = "size14",
                    tab_label = "", height = "23",
                    width = "84", required = "false",
                    value = a.value,
                    locked = "true", tab_id = "name")
                )
        elif a.type == "radio":
            if a.value == "Mr":
                isMale = True
            elif a.value == "Mrs" or a.value == "Ms":
                isMale = False
            elif a.value == "english":
                isEnglish = True

    radio_tabs_gender = [
        Radio( # DocuSign SignHere field/tab
            anchor_string = "eh_title", anchor_x_offset = 0, anchor_y_offset = 0, anchor_units = "inches", selected = isMale),
        Radio( # DocuSign SignHere field/tab
            anchor_string = "eh_title", anchor_x_offset = 0, anchor_y_offset = 0.2, anchor_units = "inches", selected = not(isMale))
        ]

    radio_group_gender = RadioGroup(
        group_name = "radio1",
        radios = radio_tabs_gender
    )

    # radio_tabs_language = [
    #     Radio( # DocuSign SignHere field/tab
    #         anchor_string = "English", anchor_x_offset = -0.29, anchor_y_offset = -0.05, anchor_units = "inches", selected = isEnglish),
    #     Radio( # DocuSign SignHere field/tab
    #         anchor_string = "Other:", anchor_x_offset = -0.29, anchor_y_offset = -0.05, anchor_units = "inches", selected = not(isEnglish))
    #     ]

    # radio_group_language = RadioGroup(
    #     group_name = "radio2",
    #     radios = radio_tabs_language
    # )

    # Create a sign_here tab (field on the document)
    sign_here = [
        SignHere( # DocuSign SignHere field/tab
            document_id = '1', page_number = '1', recipient_id = '1', tab_label = 'SignHereTab',
            anchor_string = "eh_sign_here", anchor_x_offset = 0, anchor_units = "inches",
            anchor_case_sensitive = True)
        ]

    tabsObj = Tabs(
        text_tabs = text_fields,
        radio_group_tabs = [radio_group_gender ],
        sign_here_tabs = sign_here
    )


    return tabsObj

def make_envelope(args):
    """
    Creates envelope
    args -- parameters for the envelope:
    signer_email, signer_name, signer_client_id
    returns an envelope definition
    """
    # Select PDF to display here
    # file_name = ds_config.DS_CONFIG["doc_pdf"]
    file_name = []
    file_string = ""

    for a in args["form_data"]:
        print(a.name)
        print(a.value)
        if (("pdf_" in a.name) and (a.value)):
            file_name = a.value
            break

    print("FILE NAME")
    print(file_name)
    if not file_name:
        print("ERROR: PDF FORM NOT FOUND")

    with open(path.join(demo_docs_path, file_name   ), "rb") as file:
        content_bytes = file.read()
    base64_file_content = base64.b64encode(content_bytes).decode("ascii")

    # Create the document model
    document = Document( # create the DocuSign document object
        document_base64 = base64_file_content,
        name = "Example document", # can be different from actual file name
        file_extension = "pdf", # many different document types are accepted
        document_id = 1, # a label used to reference the doc

        # SET THIS TO TRUE IF PDF HAS ADOBE FIELD NAMES!
        transform_pdf_fields = False
    )

    # Create the signer recipient model
    signer = Signer( # The signer
        email = args["signer_email"], name = args["signer_name"],
        recipient_id = "1", routing_order = "1",
        # Setting the client_user_id marks the signer as embedded
        client_user_id = args["signer_client_id"]
    )

    # print("ARGS")
    # print(args)

    # Add the tabs model (including the sign_here tab) to the signer
    # The Tabs object wants arrays of the different field/tab types
    signer.tabs = setup_tabs(signer.tabs, args["form_data"])

    # print("NEW TABS")
    # print(signer.tabs)

    #import pdb; pdb.set_trace()

    # Recipients object:
    # recipients_server_template = Recipients(
    #     signers=[signer]
    # )
    #
    # # CompositeTemplate object:
    # composite_template = CompositeTemplate(
    #     composite_template_id="1",
    #     server_templates=[
    #         ServerTemplate(sequence="1", template_id=args["template_id"])#args["template_id"])
    #     ],
    #     # Add the roles via an inlineTemplate
    #     inline_templates=[
    #         InlineTemplate(sequence="1",
    #                        recipients=recipients_server_template)
    #     ]
    # )

    # Next, create the top level envelope definition and populate it.
    envelope_definition = EnvelopeDefinition(
        email_subject = "Please sign this document sent from the Python SDK",
        # composite_templates = composite_template,
        documents = [document],
        # The Recipients object wants arrays for each recipient type
        recipients = Recipients(signers = [signer]),
        status = "sent" # requests that the envelope be created and sent.
    )

    # Store document info in session, in case we want to download the PDF at the end of the signing process
    session["envelope_documents"] = {
            "documents": [
                {
                    "document_id": 1,#envelope_definition.documents["document_id"]
                    "name": "Example Document",
                    "type": "content"
                }
            ]
        }

    # print("TABS!!")
    # print(signer.tabs)

    return envelope_definition
# ***DS.snippet.0.end


def get_controller():
    """responds with the form for the example"""

    if views.ds_token_ok():
        form = ClientForm()

        if form.validate() == False:
            flash:('All fields are required.')
        return render_template('form.html', form = form)
        # return render_template("eg001_embedded_signing.html",
        #                        title="Embedded Signing Ceremony",
        #                        source_file=path.basename(__file__),
        #                        source_url=ds_config.DS_CONFIG["github_example_url"] + path.basename(__file__),
        #                        documentation=ds_config.DS_CONFIG["documentation"] + eg,
        #                        show_doc=ds_config.DS_CONFIG["documentation"],
        #                        signer_name=ds_config.DS_CONFIG["signer_name"],
        #                        signer_email=ds_config.DS_CONFIG["signer_email"]
        # )
    else:
        # Save the current operation so it will be resumed after authentication
        session["eg"] = url_for(eg)
        return redirect(url_for("ds_must_authenticate"))



# def make_template_req():
#     """Creates template req object"""
#
#     # document 1 (pdf)
#     #
#     # The template has two recipient roles.
#     # recipient 1 - signer
#     # recipient 2 - cc
#     with open(path.join(demo_docs_path, "sample_form.pdf"), "rb") as file:
#         content_bytes = file.read()
#     base64_file_content = base64.b64encode(content_bytes).decode("ascii")
#
#     # Create the document model
#     document = Document(  # create the DocuSign document object
#         document_base64=base64_file_content,
#         name="Lorem Ipsum",  # can be different from actual file name
#         file_extension="pdf",  # many different document types are accepted
#         document_id=1  # a label used to reference the doc
#     )
#
#     # Create the signer recipient model
#     signer = Signer(role_name="signer", recipient_id="1", routing_order="1")
#
#     # Create fields using absolute positioning
#     # Create a sign_here tab (field on the document)
#     sign_here = SignHere(document_id="1", page_number="1", x_position="191", y_position="148")
#     check1 = Checkbox(
#         document_id="1",
#         page_number="1",
#         x_position="75",
#         y_position="417",
#         tab_label="ckAuthorization"
#     )
#     check2 = Checkbox(
#         document_id="1",
#         page_number="1",
#         x_position="75",
#         y_position="447",
#         tab_label="ckAuthentication"
#     )
#     check3 = Checkbox(
#         document_id="1",
#         page_number="1",
#         x_position="75",
#         y_position="478",
#         tab_label="ckAgreement"
#     )
#     check4 = Checkbox(
#         document_id="1",
#         page_number="1",
#         x_position="75",
#         y_position="508",
#         tab_label="ckAcknowledgement"
#     )
#     list1 = List(
#         document_id="1",
#         page_number="1",
#         x_position="142",
#         y_position="291",
#         font="helvetica",
#         font_size="size14",
#         tab_label="list",
#         required="false",
#         list_items=[
#             ListItem(text="Red", value="red"),
#             ListItem(text="Orange", value="orange"),
#             ListItem(text="Yellow", value="yellow"),
#             ListItem(text="Green", value="green"),
#             ListItem(text="Blue", value="blue"),
#             ListItem(text="Indigo", value="indigo"),
#             ListItem(text="Violet", value="violet")
#         ]
#     )
#     number1 = Number(
#         document_id="1",
#         page_number="1",
#         x_position="163",
#         y_position="260",
#         font="helvetica",
#         font_size="size14",
#         tab_label="numbersOnly",
#         width="84",
#         required="false"
#     )
#     radio_group = RadioGroup(
#         document_id="1",
#         group_name="radio1",
#         radios=[
#             Radio(
#                 page_number="1", x_position="142", y_position="384",
#                 value="white", required="false"
#             ),
#             Radio(
#                 page_number="1", x_position="74", y_position="384",
#                 value="red", required="false"
#             ),
#             Radio(
#                 page_number="1", x_position="220", y_position="384",
#                 value="blue", required="false"
#             )
#         ]
#     )
#     text = Text(
#         document_id="1",
#         page_number="1",
#         x_position="153",
#         y_position="230",
#         font="helvetica",
#         font_size="size14",
#         tab_label="text",
#         height="23",
#         width="84",
#         required="false"
#     )
#     # Add the tabs model to the signer
#     # The Tabs object wants arrays of the different field/tab types
#     signer.tabs = Tabs(
#         sign_here_tabs=[sign_here],
#         checkbox_tabs=[check1, check2, check3, check4],
#         list_tabs=[list1],
#         number_tabs=[number1],
#         radio_group_tabs=[radio_group],
#         text_tabs=[text]
#     )
#
#     template_name = "DJ_TEST_TEMPLATE"
#
#     # Top object:
#     template_request = EnvelopeTemplate(
#         documents=[document], email_subject="Please sign this document",
#         recipients=Recipients(signers=[signer]),
#         description="Example template created via the API",
#         name=template_name,
#         shared="false",
#         status="created"
#     )
#
#     return template_request
#
#
# def create_api_client(base_path, access_token):
#     """Create api client and construct API headers"""
#     api_client = ApiClient()
#     api_client.host = base_path
#     api_client.set_default_header(header_name="Authorization", header_value=f"Bearer {access_token}")
#
#     return api_client
