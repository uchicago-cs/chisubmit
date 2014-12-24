from wtforms import Form
from wtforms.validators import InputRequired, Optional, Length
from wtforms.fields import StringField, IntegerField,\
    FormField, FieldList, BooleanField


class CreateTeamInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    course_id = StringField(validators=[Length(max=36), InputRequired()])


class LinkProjectInput(Form):
    team_id = StringField(InputRequired())
    project_id = StringField(InputRequired())


class LinkStudentInput(Form):
    team_id = StringField(InputRequired())
    student_id = StringField(InputRequired())


class AddProjectsInput(Form):
    add = FieldList(FormField(LinkProjectInput))


class AddGradeInput(Form):
    team_id = StringField(InputRequired())
    project_id = StringField(InputRequired())
    grade_component_name = StringField(InputRequired())
    points = IntegerField(InputRequired())


class AddGradesInput(Form):
    add = FieldList(FormField(AddGradeInput))


class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))


class UpdateTeamInput(Form):
    students = FormField(AddStudentsInput)
    projects = FormField(AddProjectsInput)
    git_staging_repo_created = BooleanField()


class UpdateProjectTeamInput(Form):
    grader_id = StringField(Optional())
    grades = FormField(AddGradesInput)
