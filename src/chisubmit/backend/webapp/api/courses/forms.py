from wtforms import Form, StringField, IntegerField
from wtforms.fields import FormField, FieldList
from wtforms.validators import Length, InputRequired, NumberRange, Optional
from chisubmit.backend.webapp.api.assignments.forms import CreateAssignmentInput
from chisubmit.backend.webapp.api.teams.forms import CreateTeamInput


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


class LinkInstructorInput(Form):
    course_id = StringField(validators=[InputRequired()])
    instructor_id = StringField(validators=[InputRequired()])

class SetOptionInput(Form):
    name = StringField(validators=[InputRequired()])
    value = StringField(validators=[InputRequired()])

class AddGradersInput(Form):
    add = FieldList(FormField(LinkGraderInput))


class AddStudentsInput(Form):
    add = FieldList(FormField(LinkStudentInput))


class AddInstructorsInput(Form):
    add = FieldList(FormField(LinkInstructorInput))

class UpdateOptionInput(Form):
    update = FieldList(FormField(SetOptionInput))

class CreateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=5), InputRequired()])
    name = StringField(validators=[Length(max=36, min=5), InputRequired()])


class UpdateCourseInput(Form):
    # FIXME 10DEC14: take the primary key out of the user's hands
    id = StringField(validators=[Length(max=36, min=10), Optional()])
    name = StringField(validators=[Length(max=36, min=10), Optional()])
    assignments = FormField(AddAssignmentsInput)
    instructors = FormField(AddInstructorsInput)
    students = FormField(AddStudentsInput)
    teams = FormField(AddTeamsInput)
    graders = FormField(AddGradersInput)
    options = FormField(UpdateOptionInput)


class SearchCourseStudentInput(Form):
    course_id = StringField(InputRequired())
    student_id = StringField(InputRequired())
