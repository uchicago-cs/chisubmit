from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField, FormField, FieldList
from api.forms import ISODateTimeField


class CreateGradeComponentInput(Form):
    name = StringField(validators=[Length(max=36), InputRequired()])
    points = IntegerField(validators=[InputRequired()])
    project_id = StringField(validators=[Length(max=36), InputRequired()])


class AddGradeComponents(Form):
    add = FieldList(FormField(CreateGradeComponentInput))


class UpdateProjectInput(Form):
    id = StringField(validators=[Length(max=36, min=10), Optional()])
    name = StringField(validators=[Length(max=36, min=10), Optional()])
    deadline = ISODateTimeField(validators=[Optional()])
    grade_components = FormField(AddGradeComponents)


class CreateProjectInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    course_id = StringField('course_id',
                            validators=[Length(max=36, min=5),
                                        InputRequired()])
    deadline = ISODateTimeField(validators=[InputRequired()])
    name = StringField('name',
                       validators=[Length(max=36, min=5),
                                   InputRequired()])


class SearchProjectInput(Form):
    project_id = StringField('project_id',
                             validators=[Length(max=36, min=5),
                                         InputRequired()])
    name = StringField('name', validators=[Length(max=36, min=5), Optional()])
