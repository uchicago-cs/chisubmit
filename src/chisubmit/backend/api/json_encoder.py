from flask.json import JSONEncoder
from datetime import datetime


class CustomJSONEncoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return JSONEncoder.default(self, o)
