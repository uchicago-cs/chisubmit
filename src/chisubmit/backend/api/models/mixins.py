from flask import url_for


class ExposedModel(object):

    @classmethod
    def uri(self):
        selfname = self.__name__.lower()
        # FIXME 23JULY14: assumptions unlikely to hold
        identifier = selfname + "_id"
        return url_for('get',
                       **{identifier: getattr(self, 'course_id'),
                          '_external': True})


class UniqueModel(object):

    def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
        cache = getattr(session, '_unique_cache', None)
        if cache is None:
            session._unique_cache = cache = {}

        key = (cls, hashfunc(*arg, **kw))
        if key in cache:
            return cache[key]
        else:
            with session.no_autoflush:
                q = session.query(cls)
                q = queryfunc(q, *arg, **kw)
                obj = q.first()
                if not obj:
                    obj = constructor(*arg, **kw)
                    session.add(obj)
            cache[key] = obj
            return obj

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(session,
                       cls, cls.unique_hash,
                       cls.unique_filter, cls,
                       arg, kw)
