from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, EqualTo


class ProfileForm(FlaskForm):
    """Candidate profile editing form."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=150)
    ])
    phone = StringField('Phone Number', validators=[
        Optional(),
        Length(max=30)
    ])
    headline = StringField('Professional Headline', validators=[
        Optional(),
        Length(max=255)
    ], description='e.g., Aspiring Full Stack Python Developer | CSE Senior')
    education_level = StringField('Highest Education Level', validators=[
        Optional(),
        Length(max=100)
    ], description='e.g., B.Tech Computer Engineering')
    institution = StringField('College / Institution', validators=[
        Optional(),
        Length(max=200)
    ])
    graduation_year = IntegerField('Graduation Year', validators=[
        Optional(),
        NumberRange(min=1980, max=2035, message='Enter a valid 4-digit graduation year.')
    ])
    bio = TextAreaField('Summary / Bio', validators=[
        Optional(),
        Length(max=2000)
    ])
    submit = SubmitField('Save Profile Changes')


class ChangePasswordForm(FlaskForm):
    """Account password change form."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required.')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password.'),
        EqualTo('new_password', message='New passwords must match.')
    ])
    submit = SubmitField('Update Password')


class DeleteAccountForm(FlaskForm):
    """Account deletion confirmation form."""
    confirm_phrase = StringField('Type "DELETE" to confirm', validators=[
        DataRequired(message='Please type DELETE to confirm.')
    ])
    password = PasswordField('Enter Password to confirm', validators=[
        DataRequired(message='Password is required to delete account.')
    ])
    submit = SubmitField('Permanently Delete My Account')
