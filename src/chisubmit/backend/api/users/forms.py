from wtforms import Form
from wtforms.validators import InputRequired, Optional,\
    Length, Email
from wtforms.fields import StringField, BooleanField


class CreateUserInput(Form):
    id = StringField(validators=[Length(max=36), InputRequired()])
    first_name = StringField(validators=[Length(max=36), InputRequired()])
    last_name = StringField('last_name',
                            validators=[Length(max=36, min=1),
                                        InputRequired()])
    email = StringField(
        validators=[InputRequired(), Length(max=128, min=10), Email()])


class UpdateUserInput(Form):
    first_name = StringField(validators=[Length(max=36), InputRequired()])
    last_name = StringField('last_name',
                            validators=[Length(max=36, min=1),
                                        Optional()])
    email = StringField(
        validators=[InputRequired(), Length(max=128, min=10), Email()])

class GenerateAccessTokenInput(Form):
    reset = BooleanField(validators=[Optional()])
