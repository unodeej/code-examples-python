from flask_wtf import Form
from wtforms import TextField, IntegerField, BooleanField, TextAreaField, SubmitField, RadioField, SelectField, SelectMultipleField
from wtforms import validators, ValidationError

class ClientForm(Form):
    title = RadioField('Title', choices = [('Mr','Mr'),('Ms','Ms'),('Mrs','Mrs')])
    first_name = TextField("First Name ",[validators.Required("Please enter your first name.")])
    middle_initial = TextField("Middle Initial ")
    last_name = TextField("Last Name ",[validators.Required("Please enter your last name.")])

    home_address = TextField("Home Address")
    city = TextField("City")
    state = TextField("State")
    zip = TextField("Zip Code")

    diff_mail_addr = BooleanField('Different mailing address?')

    mailing_address = TextField("Mailing Address")
    mailing_city = TextField("City")
    mailing_state = TextField("State")
    mailing_zip = TextField("Zip Code")

    home_tel = TextField("Phone Number")

    email = TextField("Email",[validators.Required("Please enter your email address."),
    validators.Email("Please enter your email address.")])

    dob = TextField("Date of Birth ")
    aarp = TextField("AARP Membership # (Only required if you are enrolling in a AARP Medicare Supplement plan)")

    add_coverage = SelectMultipleField("Would you like to add additional coverage if not already included in your plan?", choices = [('Dental', 'Dental Coverage'), ('Vision', 'Vision Coverage'), ('More', "I'd like to learn more")] )

    claim_num = TextField("Medicare Claim Number")
    hospital_month = SelectField("Month", choices = [('Jan','January'),('Feb','February'),('Mar','March'),
                                                     ('Apr','April'),('May','May'),('Jun','June'),
                                                     ('Jul','July'),('Aug','August'),('Sep','September'),
                                                     ('Oct','October'),('Nov','November'),('Dec','December'), ] )
    hospital_year = SelectField("Year", choices = [('2020','2020'),('2019','2019'),('2018','2018'),
                                                     ('2017','2017'),('2016','2016'),('2015','2015'),
                                                     ('2014','2014'),('2013','2013'),('2012','2012'),
                                                     ('2011','2011'),('2010','2010'),('2009','2009'),
                                                     ('2008','2008'),('2007','2007'),('2006','2006'),
                                                     ('2005','2005') ] )

    medical_month = SelectField("Month", choices = [('Jan','January'),('Feb','February'),('Mar','March'),
                                                     ('Apr','April'),('May','May'),('Jun','June'),
                                                     ('Jul','July'),('Aug','August'),('Sep','September'),
                                                     ('Oct','October'),('Nov','November'),('Dec','December'), ] )
    medical_year = SelectField("Year", choices = [('2020','2020'),('2019','2019'),('2018','2018'),
                                                     ('2017','2017'),('2016','2016'),('2015','2015'),
                                                     ('2014','2014'),('2013','2013'),('2012','2012'),
                                                     ('2011','2011'),('2010','2010'),('2009','2009'),
                                                     ('2008','2008'),('2007','2007'),('2006','2006'),
                                                     ('2005','2005') ] )


    plan_type = SelectField("Type of plan", choices = [('None','None'),('Emp','Employer Group Plan'),('Ind','Individual Plan'),
                                                       ('Uni','Union Plan'),('Oth','Other') ] )
    ins_company = TextField("Health insurance company")
    policy_id = TextField("Health insurance policy ID #")
    ins_start_date = TextField("Health insurance start date (Best estimation if you can't find it)")
    ins_end_date = TextField("Health insurance end date (leave blank if your health insurance is still active)")

    pref_payment = SelectField("How would you prefer to pay?", choices = [('Mon','Monthly billing by the health insurance company'),
                                                                          ('Soc','Social Security check deduction (Not for Medicare Supplement Plans)'),
                                                                          ('Dir','Direct Debit') ] )

    submit = SubmitField("Submit")
