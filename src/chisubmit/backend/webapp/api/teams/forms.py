from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField,\
    FormField, FieldList, BooleanField


class CreateTeamInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    course_id = StringField(validators=[Length(max=36), InputRequired()])


class LinkAssignmentInput(Form):
    team_id = StringField(InputRequired())
    assignment_id = StringField(InputRequired())


class LinkStudentInput(Form):
    team_id = StringField(InputRequired())
    student_id = StringField(InputRequired())


class AddAssignmentsInput(Form):
    add = FieldList(FormField(LinkAssignmentInput))


class AddGradeInput(Form):
    team_id = StringField(InputRequired())
    assignment_id = StringField(InputRequired())
    grade_component_name = StringField(InputRequired())
    points = IntegerField(InputRequired())


class AddGradesInput(Form):
    add = FieldList(FormField(AddGradeInput))


class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))


class UpdateTeamInput(Form):
    students = FormField(AddStudentsInput)
    assignments = FormField(AddAssignmentsInput)
    git_staging_repo_created = BooleanField()


class UpdateAssignmentTeamInput(Form):
    grader_id = StringField(Optional())
    grades = FormField(AddGradesInput)
