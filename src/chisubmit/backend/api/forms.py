from wtforms import Field
from wtforms.widgets import TextInput
from dateutil.parser import parse


class ISODateTimeField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return self.data.isoformat()
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            # convert [string] datetime.isoformat() back to a datetime.
            # strptime ***CAN NOT*** and Python has no builtin. Really.
            self.data = parse(valuelist[0])
        else:
            # TODO 12DEC:14: is this impossible?
            # there's nothing valid to put in here
            self.data = ''
