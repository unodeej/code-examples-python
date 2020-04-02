from flask_wtf import Form
from wtforms import TextField, IntegerField, TextAreaField, SubmitField, RadioField, SelectField
from wtforms import validators, ValidationError

class ClientForm(Form):
   last_name = TextField("Last Name ",[validators.Required("Please enter your last name.")])
   first_name = TextField("First Name ",[validators.Required("Please enter your first name.")])

   middle_initial = TextField("Middle Initial ")

   gender = RadioField('Gender', choices = [('M','Male'),('F','Female')])

   mailing_address = TextField("Address")
   city = TextField("City")
   state = TextField("State")
   zip = TextField("Zip")
   county = TextField("County")

   home_tel = TextField("Home Phone ")

   email = TextField("Email",[validators.Required("Please enter your email address."),
   validators.Email("Please enter your email address.")])

   dob = TextField("Date of Birth ")
   ssn = TextField("Social Security Number ")

   req_start_date = TextField("Requested start date")
   pref_lang = RadioField('Preferred Language', choices = [('E','English'),('O','Other')])

   # Age = IntegerField("Age")
   # language = SelectField('Programming Languages', choices = [('java', 'Java'),('py', 'Python')])

   submit = SubmitField("Submit")
