from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField, FormField, FieldList
from chisubmit.backend.webapp.api.forms import ISODateTimeField
from wtforms.fields.core import BooleanField, FloatField


class CreateGradeComponentInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    description = StringField(validators=[InputRequired()])
    points = FloatField(validators=[InputRequired()])


class AddGradeComponents(Form):
    add = FieldList(FormField(CreateGradeComponentInput))


class UpdateAssignmentInput(Form):
    id = StringField(validators=[Length(max=36, min=2), Optional()])
    name = StringField(validators=[Length(max=36, min=2), Optional()])
    deadline = ISODateTimeField(validators=[Optional()])
    grade_components = FormField(AddGradeComponents)


class CreateAssignmentInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    deadline = ISODateTimeField(validators=[InputRequired()])
    name = StringField('name',
                       validators=[Length(max=36, min=2),
                                   InputRequired()])


class SearchAssignmentInput(Form):
    assignment_id = StringField('assignment_id',
                             validators=[Length(max=36, min=2),
                                         InputRequired()])
    name = StringField('name', validators=[Length(max=36, min=2), Optional()])


class RegisterAssignmentInput(Form):
    team_name = StringField(validators=[Length(max=36, min=2), Optional()])
    partners = FieldList(StringField())
    
class SubmitAssignmentInput(Form):
    team_id = StringField(validators=[Length(max=36, min=2),InputRequired()])
    commit_sha = StringField(validators=[Length(max=40, min=20),InputRequired()])
    extensions = IntegerField(default=0)
    dry_run = BooleanField(default=False)
        
class CancelSubmitAssignmentInput(Form):
    team_id = StringField(validators=[Length(max=36, min=2),InputRequired()])

