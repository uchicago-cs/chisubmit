from wtforms import Form, StringField, IntegerField
from wtforms.fields import FormField, FieldList
from wtforms.validators import Length, InputRequired, NumberRange, Optional
from chisubmit.backend.webapp.api.assignments.forms import CreateAssignmentInput
from chisubmit.backend.webapp.api.teams.forms import CreateTeamInput
from wtforms.fields.core import BooleanField


class SetOptionInput(Form):
    name = StringField(validators=[InputRequired()])
    value = StringField(validators=[InputRequired()])


class AddTeamsInput(Form):
    add = FieldList(FormField(CreateTeamInput))


class AddAssignmentsInput(Form):
    add = FieldList(FormField(CreateAssignmentInput))


class LinkGraderInput(Form):
    course_id = StringField(validators=[InputRequired()])
    grader_id = StringField(validators=[InputRequired()])


class LinkStudentInput(Form):
    course_id = StringField(validators=[InputRequired()])
    student_id = StringField(validators=[InputRequired()])

class UpdateStudentInput(Form):
    student_id = StringField(default = None)
    dropped = BooleanField(validators=[Optional()])
    repo_info = FieldList(FormField(SetOptionInput))

class UpdateInstructorInput(Form):
    instructor_id = StringField(default = None)
    repo_info = FieldList(FormField(SetOptionInput))

class UpdateGraderInput(Form):
    grader_id = StringField(default = None)
    repo_info = FieldList(FormField(SetOptionInput))
    conflicts = StringField(validators=[Optional()])


class LinkInstructorInput(Form):
    course_id = StringField(validators=[InputRequired()])
    instructor_id = StringField(validators=[InputRequired()])


class AddGradersInput(Form):
    add = FieldList(FormField(LinkGraderInput))
    update = FieldList(FormField(UpdateGraderInput))


class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))
    update = FieldList(FormField(UpdateStudentInput))


class AddInstructorsInput(Form):
    add = FieldList(FormField(LinkInstructorInput))
    update = FieldList(FormField(UpdateInstructorInput))


class UpdateOptionInput(Form):
    update = FieldList(FormField(SetOptionInput))

class CreateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=2), InputRequired()])
    name = StringField(validators=[Length(max=36, min=2), InputRequired()])


class UpdateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=2), Optional()])
    name = StringField(validators=[Length(max=36, min=2), Optional()])
    assignments = FormField(AddAssignmentsInput)
    instructors = FormField(AddInstructorsInput)
    students = FormField(AddStudentsInput)
    teams = FormField(AddTeamsInput)
    graders = FormField(AddGradersInput)
    options = FormField(UpdateOptionInput)


class SearchCourseStudentInput(Form):
    course_id = StringField(InputRequired())
    student_id = StringField(InputRequired())
