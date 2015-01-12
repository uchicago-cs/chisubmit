from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField,\
    FormField, FieldList, BooleanField
from wtforms.fields.core import FloatField


class CreateTeamInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    course_id = StringField(validators=[Length(max=36), InputRequired()])


class LinkAssignmentInput(Form):
    team_id = StringField(InputRequired())
    assignment_id = StringField(InputRequired())


class LinkStudentInput(Form):
    team_id = StringField(InputRequired())
    student_id = StringField(InputRequired())

class UpdateAssignmentTeamInput(Form):
    assignment_id = StringField(InputRequired())
    grader_id = StringField(Optional())

class AddAssignmentsInput(Form):
    add = FieldList(FormField(LinkAssignmentInput))
    update = FieldList(FormField(UpdateAssignmentTeamInput))


class AddPenaltiesInput(Form):
    assignment_id = StringField(InputRequired())
    penalties = StringField(InputRequired())

class AddGradeInput(Form):
    assignment_id = StringField(InputRequired())
    grade_component_id = StringField(InputRequired())
    points = FloatField(InputRequired())


class AddGradesInput(Form):
    add = FieldList(FormField(AddGradeInput))
    penalties = FieldList(FormField(AddPenaltiesInput))

class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))

class SetOptionInput(Form):
    name = StringField(validators=[InputRequired()])
    value = StringField(validators=[InputRequired()])

class UpdateTeamInput(Form):
    students = FormField(AddStudentsInput)
    assignments = FormField(AddAssignmentsInput)
    grades = FormField(AddGradesInput)
    extras = FieldList(FormField(SetOptionInput))
    active = BooleanField(validators=[Optional()])


