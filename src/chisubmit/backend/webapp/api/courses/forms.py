from wtforms import Form, StringField, IntegerField
from wtforms.fields import FormField, FieldList
from wtforms.validators import Length, InputRequired, NumberRange, Optional
from api.projects.forms import CreateProjectInput
from api.teams.forms import CreateTeamInput


class AddTeamsInput(Form):
    add = FieldList(FormField(CreateTeamInput))


class AddProjectsInput(Form):
    add = FieldList(FormField(CreateProjectInput))


class LinkGraderInput(Form):
    course_id = StringField(validators=[InputRequired()])
    grader_id = StringField(validators=[InputRequired()])


class LinkStudentInput(Form):
    course_id = StringField(validators=[InputRequired()])
    student_id = StringField(validators=[InputRequired()])


class LinkInstructorInput(Form):
    course_id = StringField(validators=[InputRequired()])
    instructor_id = StringField(validators=[InputRequired()])


class AddGradersInput(Form):
    add = FieldList(FormField(LinkGraderInput))


class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))


class AddInstructorsInput(Form):
    add = FieldList(FormField(LinkInstructorInput))


class CreateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=5), InputRequired()])
    name = StringField(validators=[Length(max=36, min=5), InputRequired()])
    extensions = IntegerField(validators=[NumberRange(max=25), Optional()])
    git_server_connection_string = StringField(
        validators=[Length(max=120, min=10), Optional()])
    git_staging_server_connection_string = StringField(
        validators=[Length(max=120, min=10), Optional()])


class UpdateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=10), Optional()])
    name = StringField(validators=[Length(max=36, min=10), Optional()])
    extensions = IntegerField(
        validators=[NumberRange(max=25, min=0), Optional()])
    git_server_connection_string = StringField(
        validators=[Length(max=120, min=10), Optional()])
    git_staging_server_connection_string = StringField(
        validators=[Length(max=120, min=10), Optional()])
    projects = FormField(AddProjectsInput)
    instructors = FormField(AddInstructorsInput)
    students = FormField(AddStudentsInput)
    teams = FormField(AddTeamsInput)
    graders = FormField(AddGradersInput)


class SearchCourseStudentInput(Form):
    course_id = StringField(InputRequired())
    student_id = StringField(InputRequired())
