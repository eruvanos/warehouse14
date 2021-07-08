from flask_wtf import FlaskForm
from wtforms import StringField, RadioField
from wtforms.validators import DataRequired


class CreateProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired()])
    public = RadioField(
        "Mode", choices=[(False, "Private"), (True, "Public")], default=False
    )


class CreateAPITokenForm(FlaskForm):
    name = StringField(validators=[DataRequired()], label="What is this token for?")
