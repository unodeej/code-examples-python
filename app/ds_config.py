# ds_config.py
#
# DocuSign configuration settings
import os

DS_CONFIG = {
    "ds_client_id": "5289ffe6-e63e-46c9-9d0d-0c9cfdfcaa2c", # The app's DocuSign integration key
    "ds_client_secret": "b1f594a1-ceeb-4498-bc07-090b75ab35c1", # The app's DocuSign integration key's secret
    "signer_email": "unodeej@gmail.com",
    "signer_name": "DJ Uno",
    "app_url": "http://localhost:5000", # The url of the application. Eg http://localhost:5000
    # NOTE: You must add a Redirect URI of appUrl/ds/callback to your Integration Key.
    #       Example: http:#localhost:5000/ds/callback
    "authorization_server": "https://account-d.docusign.com",
    "session_secret": "abcdef", # Secret for encrypting session cookie content
                                          # Use any random string of characters
    "allow_silent_authentication": True, # a user can be silently authenticated if they have an
    # active login session on another tab of the same browser
    "target_account_id": None, # Set if you want a specific DocuSign AccountId,
                               # If None, the user's default account will be used.
    "demo_doc_path": "demo_documents",
    "doc_salary_docx": "World_Wide_Corp_salary.docx",
    "doc_docx": "World_Wide_Corp_Battle_Plan_Trafalgar.docx",
    "doc_pdf":  "sample_form.pdf",
    # Payment gateway information is optional
    "gateway_account_id": "{DS_PAYMENT_GATEWAY_ID}",
    "gateway_name": "stripe",
    "gateway_display_name": "Stripe",
    "github_example_url": "https://github.com/docusign/eg-03-python-auth-code-grant/tree/master/app/",
    "documentation": "" # Use an empty string to indicate no documentation path.
}
