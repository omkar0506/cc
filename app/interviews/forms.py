from flask_wtf import FlaskForm
from wtforms import SelectField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length


class InterviewConfigForm(FlaskForm):
    """Initial interview configuration form."""
    job_role_id = SelectField('Target Job Role', coerce=int, validators=[DataRequired()])
    category = SelectField('Interview Category', choices=[
        ('technical', 'Technical & Conceptual (includes written code problems)'),
        ('hr', 'HR, Behavioral & Situational (STAR Method)')
    ], default='technical')
    target_difficulty = SelectField('Starting Difficulty Preference', choices=[
        ('adaptive', 'Fully Adaptive (Starts Medium, adjusts dynamically)'),
        ('easy', 'Foundational (Starts Easy)'),
        ('medium', 'Standard (Starts Medium)'),
        ('hard', 'Advanced (Starts Hard)')
    ], default='adaptive')
    total_questions_limit = IntegerField('Number of Questions (3 to 10)', default=5, validators=[
        DataRequired(),
        NumberRange(min=3, max=10, message='Interview length must be between 3 and 10 questions.')
    ])
    resume_id = SelectField('Linked Resume (Optional for claim verification)', coerce=int)
    submit = SubmitField('Proceed to Self-Assessment &rarr;')


class AnswerSubmissionForm(FlaskForm):
    """Candidate answer submission form."""
    answer_text = TextAreaField('Your Answer', validators=[
        DataRequired(message='Please provide an answer before submitting.'),
        Length(min=5, max=10000, message='Answer must be at least 5 characters.')
    ])
    submit = SubmitField('Submit Answer & Evaluate &rarr;')
