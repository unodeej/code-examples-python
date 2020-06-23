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
import smtplib
from email.message import EmailMessage
import boto3
import urllib
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Global OAuth variables

eg = "eg001"  # reference (and url) for this example
signer_client_id = 1000 # Used to indicate that the signer will use an embedded
                        # Signing Ceremony. Represents the signer's userId within
                        # your application.
authentication_method = "None" # How is this application authenticating
                               # the signer? See the 'authenticationMethod' definition
                               # https://developers.docusign.com/esign-rest-api/reference/Envelopes/EnvelopeViews/createRecipient

demo_docs_path = path.abspath(path.join(path.dirname(path.realpath(__file__)), "static/demo_documents"))


# Global spreadsheet variables

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("ehTestSheet-29bac4a93378.json", scope)
client = gspread.authorize(creds)

sheet = client.open("eh_test_sheet").sheet1

data = sheet.get_all_records()




class FormEntry():
    value = ""

    def __init__(self, type, name, anchor):
        self.type = type
        self.name = name
        self.anchor = anchor



def controller():
    """Controller router using the HTTP method"""
    if request.method == "GET":
        return get_controller()
    else:
        return render_template("404.html"), 404


def get_controller():
    """responds with the form for the example"""

    if views.ds_token_ok():
        form = ClientForm()

        if form.validate() == False:
            flash:('All fields are required.')

        return render_template('form.html', form = form)
    else:
        # Save the current operation so it will be resumed after authentication
        session["eg"] = url_for(eg)
        return redirect(url_for("ds_login"))

def create_controller():
    """
    1. Check the token
    2. Call the worker method
    3. Redirect the user to the signing ceremony
    """

    # Names of the variables from forms.py
    form_variable_names = [
        FormEntry("select", "pdf_aaatest", "eh_pdf_aaatest"),
        FormEntry("select", "pdf_aarp", "eh_pdf_name"),
        FormEntry("select", "pdf_aetna", "eh_pdf_name"),
        FormEntry("select", "pdf_alignment", "eh_pdf_name"),
        FormEntry("select", "pdf_anthem", "eh_pdf_name"),

        FormEntry("bool", "include_SOA", "eh_include_SOA"),

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


    minimum_buffer_min = 3
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
            error_body_json = err and hasattr(err, "body") and err.body
            # we can pull the DocuSign error code and message from the response body
            error_body = json.loads(error_body_json)
            error_code = error_body and "errorCode" in error_body and error_body["errorCode"]
            error_message = error_body and "message" in error_body and error_body["message"]


            print("ERROR FROM WORKER(): " + error_message)

            # views.ds_logout_internal();

            # session["eg"] = url_for("success")      # <-- problem: this works, except that our new request doesn't have the form data. Re-think architecture here.
            return views.ds_callback()#views.ds_login();

        if results:
            # Redirect the user to the Signing Ceremony
            # Don"t use an iFrame!
            # State can be stored/recovered using the framework's session or a
            # query parameter on the returnUrl (see the makeRecipientViewRequest method)


            session["envelope_id"] = results["envelope_id"]

            url = ("signing_ceremony/" +
                str(session["envelope_id"]) + "/" +
                str(args["account_id"]) )

            sign_later_url = request.base_url.replace("success", "") + url

            return render_template('form_submitted.html', sign_now_url=results["redirect_url"], sign_later_url=sign_later_url)

    else:
        print("must_authenticate")
        flash("Sorry, you need to re-authenticate.")
        # We could store the parameters of the requested operation
        # so it could be restarted automatically.
        # But since it should be rare to have a token issue here,
        # we'll make the user re-enter the form data after
        # authentication.
        session["eg"] = url_for(eg)
        return redirect(url_for("ds_login"))

# ***DS.snippet.0.start
def worker(args):
    """
    1. Create the envelope request object
    2. Send the envelope
    3. Create the Recipient View request object
    4. Obtain the recipient_view_url for the signing ceremony
    """
    envelope_args = args["envelope_args"]

    # 1. Create the envelope request object
    envelope_definition = make_envelope(envelope_args)

    # 2. call Envelopes::create API method
    # Exceptions will be caught by the calling function
    api_client = ApiClient()
    api_client.host = args["base_path"]
    api_client.set_default_header("Authorization", "Bearer " + args["ds_access_token"])

    envelope_api = EnvelopesApi(api_client)
    results = envelope_api.create_envelope(args["account_id"], envelope_definition=envelope_definition)

    envelope_id = results.envelope_id
    app.logger.info(f"Envelope was created. EnvelopeId {envelope_id}")

    view_req = create_view_request(envelope_id, args["account_id"], envelope_args["signer_client_id"], envelope_args["ds_return_url"], envelope_args["signer_name"], envelope_args["signer_email"], envelope_api)

    # STORE ENVELOPE ARGS IN SESSION! This may be insecure; don't leave confidential client data exposed!
    print("ENV ARGS")
    print(envelope_args['form_data'])
    csv_data = []
    google_form_data = []
    for f in envelope_args['form_data']:
        csv_data.append( [f.name, f.value] )
        google_form_data.append( f.value )
    session["csv_data"] = csv_data

    sheet.insert_row(google_form_data, 2)

    return view_req

def get_pdf_form():
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

    return temp_file

def get_csv_file(file_name):
    with open(file_name, mode='w') as csv_file:
        si = io.StringIO()
        writer = csv.writer(si) #csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        for d in session["csv_data"]:
            writer.writerow(d)

        return si.getvalue()

    # {'mimetype': mimetype, 'doc_name': doc_name, 'data': temp_file}
def download_doc(doc_name):
    file = get_pdf_form()
    return send_file(file, attachment_filename=doc_name)

def download_csv():
    # whatever we want to call the new file
    file_name = 'data.csv'

    val = get_csv_file(file_name)

    output = make_response(val)

    output.headers["Content-Disposition"] = "attachment; filename=" + file_name
    output.headers["Content-type"] = "text/csv"

    return output

def aws_upload(data, bucket_name, object_name):
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    expiration = 3600          # time in seconds for the url to remain valid


    s3.Bucket(bucket_name).put_object(Key=object_name, Body=data)

    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except:
        print("ERROR: S3 Client rejected presigned url request")
        return None

    return response

def send_email():
    # important, you need to send it to a server that knows how to send e-mails for you
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    # don't know how to do it without cleartexting the password and not relying on some json file that you dont git control...
    server.login('unodeej.app.test@gmail.com', 'cwecwooygqrusokv')
    msg = EmailMessage()

    # Upload the files to AWS, then get a link to the files that were uploaded
    bucket_name = 'enrollhero-test'
    object_name = 'AARPTESTDOC.csv'

    data = get_csv_file("TEST.csv")
    print(data)
    resource_url = aws_upload(data, bucket_name, object_name)

    msg.set_content(resource_url)

    msg['Subject'] = 'TEST'
    msg['From'] = 'djisawesome0@gmail.com'
    msg['To'] = "unodeej@gmail.com"
    server.send_message(msg)

    flash:('Email sent to unodeej@gmail.com.')

    return redirect(url_for("ds_return"))









def create_view_request(envelope_id, account_id, signer_client_id, return_url, signer_name, signer_email, envelope_api):
    # 3. Create the Recipient View request object
    recipient_view_request = RecipientViewRequest(
        authentication_method = authentication_method,
        client_user_id = signer_client_id,
        recipient_id = "1",
        return_url = return_url,
        user_name = signer_name, email = signer_email
    )
    # 4. Obtain the recipient_view_url for the signing ceremony
    # Exceptions will be caught by the calling function
    results = envelope_api.create_recipient_view(account_id, envelope_id,
        recipient_view_request = recipient_view_request)

    # print("ENVELOPE DEFINITION")
    # print(envelope_definition.documents)

    # print ("MYURL" + results.url)
    return {"envelope_id": envelope_id, "redirect_url": results.url}


def signing_ceremony(envelope_id, account_id):
    print("SIGN CEREMONY ~~~")

    base_path = session["ds_base_path"]
    return_url = url_for("ds_return", _external=True)
    signer_name = "David Uno"
    signer_email = "unodeej@gmail.com"

    # Authenticate (login/logout?)
    access_token = session["ds_access_token"]

    api_client = ApiClient()
    api_client.host = base_path
    api_client.set_default_header("Authorization", "Bearer " + access_token)
    envelope_api = EnvelopesApi(api_client)



    view_req = create_view_request(envelope_id, account_id, signer_client_id, return_url, signer_name, signer_email, envelope_api)

    return redirect(view_req["redirect_url"])



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
                    anchor_string = a.anchor, anchor_x_offset = 0, anchor_y_offset = -0.1, anchor_units = "inches",
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

    include_SOA = False

    for a in args["form_data"]:
        # print(a.name)
        # print(a.value)
        if (("pdf_" in a.name) and (a.value)):
            file_name = a.value
        elif a.name == "include_SOA":
            include_SOA = a.value

    print("FILE NAME")
    print(file_name)
    if not file_name:
        print("ERROR: PDF FORM NOT FOUND")

    documents = []

    if include_SOA:
        # This document gets included with every envelope
        with open(path.join(demo_docs_path, "Other/other/scope_of_appointment.pdf"), "rb") as file:
            content_bytes = file.read()
        base64_file_content = base64.b64encode(content_bytes).decode("ascii")

        scope_of_appt_doc = Document(
            document_base64 = base64_file_content,
            name = "Example document", # can be different from actual file name
            file_extension = "pdf", # many different document types are accepted
            document_id = 1, # a label used to reference the doc
        )

        documents.append(scope_of_appt_doc)


    if not file_name:
        print("ERROR: No file was selected") # WE should redirect back to the form in this case
    with open(path.join(demo_docs_path, file_name   ), "rb") as file:
        content_bytes = file.read()
    base64_file_content = base64.b64encode(content_bytes).decode("ascii")
    # Create the document model
    doc = Document( # create the DocuSign document object
        document_base64 = base64_file_content,
        name = "Example document", # can be different from actual file name
        file_extension = "pdf", # many different document types are accepted
        document_id = 1, # a label used to reference the doc

        # SET THIS TO TRUE IF PDF HAS ADOBE FIELD NAMES!
        transform_pdf_fields = False
    )

    documents.append(doc)




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
        documents = documents,
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
