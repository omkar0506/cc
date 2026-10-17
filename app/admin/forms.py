import json
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, FloatField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError
from app.models.job import JobRole, Skill


class JobRoleForm(FlaskForm):
    """Job role creation and editing form."""
    title = StringField('Role Title', validators=[
        DataRequired(message='Title is required.'),
        Length(min=2, max=150)
    ])
    slug = StringField('URL Slug', validators=[
        DataRequired(message='Slug is required.'),
        Length(min=2, max=150)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required.'),
        Length(min=10, max=2000)
    ])
    experience_level = SelectField('Experience Level', choices=[
        ('Entry-Level', 'Entry-Level'),
        ('Entry to Mid-Level', 'Entry to Mid-Level'),
        ('Mid-Level', 'Mid-Level'),
        ('Senior', 'Senior')
    ], default='Entry to Mid-Level')
    interview_topics_raw = TextAreaField('Interview Topics (one per line)', validators=[Optional()])
    easy_pct = IntegerField('Easy %', default=30, validators=[NumberRange(min=0, max=100)])
    medium_pct = IntegerField('Medium %', default=50, validators=[NumberRange(min=0, max=100)])
    hard_pct = IntegerField('Hard %', default=20, validators=[NumberRange(min=0, max=100)])
    is_active = BooleanField('Active Role', default=True)
    submit = SubmitField('Save Job Role')

    def validate_difficulty(self):
        """Ensure difficulty percentages sum to 100%."""
        total = (self.easy_pct.data or 0) + (self.medium_pct.data or 0) + (self.hard_pct.data or 0)
        if total != 100:
            raise ValidationError(f'Difficulty distribution must sum to 100% (currently {total}%).')


class SkillForm(FlaskForm):
    """Normalized skill registry form with alias configuration."""
    name = StringField('Skill Name', validators=[
        DataRequired(message='Skill name is required.'),
        Length(min=2, max=100)
    ])
    slug = StringField('URL Slug', validators=[
        DataRequired(message='Slug is required.'),
        Length(min=2, max=100)
    ])
    category = SelectField('Category', choices=[
        ('technical', 'Technical Competency'),
        ('hr', 'HR / Behavioral'),
        ('situational', 'Situational Judgment')
    ], default='technical')
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    aliases_raw = TextAreaField('Synonyms & Aliases (comma-separated)', validators=[Optional()],
                                description='e.g., Python 3, Py, CPython')
    submit = SubmitField('Save Skill')


class JobRoleSkillForm(FlaskForm):
    """Link a skill to a job role with weight and required flag."""
    skill_id = SelectField('Skill', coerce=int, validators=[DataRequired()])
    importance_weight = FloatField('Importance Weight (1.0 - 5.0)', default=1.0, validators=[
        DataRequired(),
        NumberRange(min=0.5, max=5.0, message='Weight must be between 0.5 and 5.0')
    ])
    is_required = BooleanField('Required Skill', default=True)
    submit = SubmitField('Add Skill Link')


class QuestionForm(FlaskForm):
    """Question bank management form with rubric and concept schema validation."""
    job_role_id = SelectField('Job Role', coerce=int, validators=[DataRequired()])
    skill_id = SelectField('Competency / Skill', coerce=int, validators=[DataRequired()])
    question_type = SelectField('Question Type', choices=[
        ('technical', 'Technical Theory / Conceptual'),
        ('code-written', 'Written Code / Implementation (not execution verified)'),
        ('hr', 'Behavioral / Situational (STAR)')
    ], default='technical')
    difficulty = SelectField('Difficulty Level', choices=[
        ('easy', 'Easy / Foundational'),
        ('medium', 'Medium / Intermediate'),
        ('hard', 'Hard / Advanced')
    ], default='medium')
    question_text = TextAreaField('Question Text', validators=[
        DataRequired(message='Question text is required.'),
        Length(min=10, max=3000)
    ])
    expected_concepts_raw = TextAreaField('Expected Concepts (one per line)', validators=[
        DataRequired(message='At least one expected concept is required.')
    ], description='Key concepts/keywords expected in a competent answer')
    reference_answer = TextAreaField('Reference Answer / Solution Guide', validators=[
        DataRequired(message='Reference answer is required.'),
        Length(min=10, max=5000)
    ])
    rubric_raw = TextAreaField('Rubric JSON Definition', validators=[Optional()],
                               description='Optional JSON mapping criterion names to weights (e.g. {"correctness": 0.4, "clarity": 0.3, "depth": 0.3})')
    max_score = FloatField('Max Score', default=10.0, validators=[
        DataRequired(),
        NumberRange(min=1.0, max=100.0)
    ])
    is_approved = BooleanField('Approved Question', default=True)
    is_active = BooleanField('Active in Question Pool', default=True)
    submit = SubmitField('Save Question')

    def validate_rubric_raw(self, field):
        """Validate JSON format if rubric is provided."""
        if field.data and field.data.strip():
            try:
                parsed = json.loads(field.data.strip())
                if not isinstance(parsed, dict):
                    raise ValidationError('Rubric must be a JSON object (dictionary) of criterion weights.')
            except json.JSONDecodeError as e:
                raise ValidationError(f'Invalid JSON syntax: {e}')


class UserManagementForm(FlaskForm):
    """Admin user account editing form."""
    role = SelectField('User Role', choices=[
        ('candidate', 'Candidate'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    is_active = BooleanField('Account Active')
    submit = SubmitField('Update User')
