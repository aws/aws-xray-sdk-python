from builtins import super
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session, sessionmaker
from .util.decorators import xray_on_call, decorate_all_functions


@decorate_all_functions(xray_on_call)
class XRaySession(Session):
    pass


@decorate_all_functions(xray_on_call)
class XRayQuery(Query):
    pass


@decorate_all_functions(xray_on_call)
class XRaySessionMaker(sessionmaker):
    def __init__(self, bind=None, class_=XRaySession, autoflush=True,
                 autocommit=False,
                 expire_on_commit=True,
                 info=None, **kw):
        kw['query_cls'] = XRayQuery
        super().__init__(
            bind=bind,
            class_=class_,
            autoflush=autoflush,
            autocommit=autocommit,
            expire_on_commit=expire_on_commit,
            info=info,
            **kw
        )
