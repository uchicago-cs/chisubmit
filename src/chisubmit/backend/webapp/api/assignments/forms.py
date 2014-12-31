from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField, FormField, FieldList
from chisubmit.backend.webapp.api.forms import ISODateTimeField


class CreateGradeComponentInput(Form):
    name = StringField(validators=[Length(max=36), InputRequired()])
    points = IntegerField(validators=[InputRequired()])
    assignment_id = StringField(validators=[Length(max=36), InputRequired()])


class AddGradeComponents(Form):
    add = FieldList(FormField(CreateGradeComponentInput))


class UpdateAssignmentInput(Form):
    id = StringField(validators=[Length(max=36, min=10), Optional()])
    name = StringField(validators=[Length(max=36, min=10), Optional()])
    deadline = ISODateTimeField(validators=[Optional()])
    grade_components = FormField(AddGradeComponents)


class CreateAssignmentInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    deadline = ISODateTimeField(validators=[InputRequired()])
    name = StringField('name',
                       validators=[Length(max=36, min=5),
                                   InputRequired()])


class SearchAssignmentInput(Form):
    assignment_id = StringField('assignment_id',
                             validators=[Length(max=36, min=5),
                                         InputRequired()])
    name = StringField('name', validators=[Length(max=36, min=5), Optional()])


class RegisterAssignmentInput(Form):
    team_name = StringField(validators=[Length(max=36, min=4), Optional()])
    partners = FieldList(StringField())
