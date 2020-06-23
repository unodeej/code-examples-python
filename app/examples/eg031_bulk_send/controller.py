import base64
from os import path

from docusign_esign import EnvelopesApi, Document, Signer, EnvelopeDefinition, Recipients, \
    BulkEnvelopesApi, TextCustomField, CustomFields
from docusign_esign.models import BulkSendingCopy, BulkSendingList, BulkSendingCopyRecipient, BulkSendRequest
from flask import request, session

from ...consts import demo_docs_path, pattern
from ...docusign import create_api_client
from ...ds_config import DS_CONFIG

class Eg031Controller:
    @staticmethod
    def get_args():
        # More data validation would be a good idea here
        # Strip anything other than the characters listed
        signer_email_1 = pattern.sub("", request.form.get("signer_email_1"))
        signer_name_1 = pattern.sub("", request.form.get("signer_name_1"))
        cc_email_1 = pattern.sub("", request.form.get("cc_email_1"))
        cc_name_1 = pattern.sub("", request.form.get("cc_name_1"))
        signer_email_2 = pattern.sub("", request.form.get("signer_email_2"))
        signer_name_2 = pattern.sub("", request.form.get("signer_name_2"))
        cc_email_2 = pattern.sub("", request.form.get("cc_email_2"))
        cc_name_2 = pattern.sub("", request.form.get("cc_name_2"))

        args = {
            "account_id": session["ds_account_id"],  # Represents your {ACCOUNT_ID}
            "base_path": session["ds_base_path"],
            "access_token": session["ds_access_token"],  # Represents your {ACCESS_TOKEN}
            "signers": [{
                "signer_name": signer_name_1,
                "signer_email": signer_email_1,
                "cc_email": cc_email_1,
                "cc_name": cc_name_1
            },
                {
                    "signer_name": signer_name_2,
                    "signer_email": signer_email_2,
                    "cc_email": cc_email_2,
                    "cc_name": cc_name_2
                }
            ]

        }
        return args

    @classmethod
    def worker(cls, args):
        """
        1. Create an api client and construct API clients
        2. Create and submit a bulk sending list
        3. Create a draft envelope
        4. Add custom fields to the envelope
        5. Add recipients to the envelope
        6. Initiate bulk envelope sending
        7. Confirm sending success
        """

        # Step 2. Construct your API headers
        api_client = create_api_client(base_path=args["base_path"], access_token=args["access_token"])

        # Step 3. Submit a bulk list
        bulk_envelopes_api = BulkEnvelopesApi(api_client)
        bulk_sending_list = cls.create_bulk_sending_list(args["signers"])
        bulk_list = bulk_envelopes_api.create_bulk_send_list(
            account_id=args["account_id"],
            bulk_sending_list=bulk_sending_list
        )
        bulk_list_id = bulk_list.list_id

        # Step 4. Create an envelope
        envelope_api = EnvelopesApi(api_client)
        envelope_definition = cls.make_draft_envelope()
        envelope = envelope_api.create_envelope(account_id=args["account_id"], envelope_definition=envelope_definition)
        envelope_id = envelope.envelope_id

        # Step 5. Attach your bulk list id to the envelope
        text_custom_fields = TextCustomField(name="mailingListId", required="false", show="false", value=bulk_list_id)
        custom_fields = CustomFields(list_custom_fields=[], text_custom_fields=[text_custom_fields])
        envelope_api.create_custom_fields(
            account_id=args["account_id"],
            envelope_id=envelope_id,
            custom_fields=custom_fields
        )

        # Step 6. Add placeholder recipients
        cc = Signer(
            name="Multi Bulk Recipient::cc",
            email="multiBulkRecipients-cc@docusign.com",
            role_name="cc",
            note="",
            routing_order="1",
            status="created",
            delivery_method="email",
            recipient_id="12",
            recipient_type="signer"
        )

        signer = Signer(
            name="Multi Bulk Recipient::signer",
            email="multiBulkRecipients-signer@docusign.com",
            role_name="signer",
            note="",
            routing_order="1",
            status="created",
            delivery_method="email",
            recipient_id="13",
            recipient_type="signer"
        )

        envelope_api.create_recipient(
            account_id=args["account_id"],
            envelope_id=envelope_id,
            recipients=Recipients(signers=[signer, cc])
        )

        # Step 7. Initiate bulk send
        bulk_send_request = BulkSendRequest(envelope_or_template_id=envelope_id)
        batch = bulk_envelopes_api.create_bulk_send_request(
            account_id=args["account_id"],
            bulk_send_list_id=bulk_list_id,
            bulk_send_request=bulk_send_request
        )
        batch_id = batch.batch_id

        # Step 8. Confirm successful batch send
        response = bulk_envelopes_api.get(account_id=args["account_id"], batch_id=batch_id)

        return response

    @classmethod
    def create_bulk_sending_list(cls, args):
        """
        1. Create recipient objects with signers
        2. Create recipient objects with ccs
        3. Create bulk copies objects
        4. Create the bulk sending list object
        """

        bulk_copies = []
        for signer in args:
            recipient_1 = BulkSendingCopyRecipient(
                role_name="signer",
                tabs=[],
                name=signer["signer_name"],
                email=signer["signer_email"]
            )

            recipient_2 = BulkSendingCopyRecipient(
                role_name="cc",
                tabs=[],
                name=signer["cc_name"],
                email=signer["cc_email"]
            )

            bulk_copy = BulkSendingCopy(
                recipients=[recipient_1, recipient_2],
                custom_fields=[]
            )

            bulk_copies.append(bulk_copy)

        bulk_sending_list = BulkSendingList(
            name="sample",
            bulk_copies=bulk_copies
        )

        return bulk_sending_list

    @classmethod
    def make_draft_envelope(cls):
        """
            Creates the envelope
        """

        # Open the example file
        with open(path.join(demo_docs_path, DS_CONFIG["doc_pdf"]), "rb") as file:
            content_bytes = file.read()
        base64_file_content = base64.b64encode(content_bytes).decode("ascii")

        document = Document(
            document_base64=base64_file_content,
            name="lorem",
            file_extension="pdf",
            document_id=2
        )

        envelope_definition = EnvelopeDefinition(
            email_subject="Please Sign",
            documents=[document],
            status="created",
            envelope_id_stamping="true",
            recipients={},
        )

        return envelope_definition