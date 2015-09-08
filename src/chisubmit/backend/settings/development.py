from defaults import *

SECRET_KEY = '0jd7t0(05@5d#-7$#w2#zagfruos0r!&t37%9m)_9^#ymg7dq+'

DEBUG = True

ALLOWED_HOSTS = []

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
