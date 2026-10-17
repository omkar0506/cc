from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Candidate and Admin login form."""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please provide a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegisterForm(FlaskForm):
    """Candidate self-registration form."""
    full_name = StringField('Full Name', validators=[
        DataRequired(message='Full name is required.'),
        Length(min=2, max=150, message='Name must be between 2 and 150 characters.')
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Please provide a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.'),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password.'),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        """Ensure email is unique in users table."""
        existing = User.query.filter_by(email=field.data.lower().strip()).first()
        if existing:
            raise ValidationError('An account with this email address already exists.')
