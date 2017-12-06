from __future__ import print_function
from builtins import super
from aws_xray_sdk.core import xray_recorder
from sqlalchemy.orm.base import _generative
from sqlalchemy.orm.query import Query
from functools import wraps

class XRayQuery(Query):
    """Class overrides the Query class in SQLAlchemy 
    
    Adds X-Ray capture and SQL metadata to captures"""
    
    @xray_recorder.capture('SQLAlchemy-subquery')
    def subquery(self, name=None, with_labels=False, reduce_columns=False):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().subquery(name, with_labels, reduce_columns)

    @xray_recorder.capture('SQLAlchemy-cte')
    def cte(self, name=None, recursive=False):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().cte(name, recursive)

    @xray_recorder.capture('SQLAlchemy-label')
    def label(self, name):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().label(name)

    @xray_recorder.capture('SQLAlchemy-as_scalar')
    def as_scalar(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().as_scalar()
   
    @_generative()
    @xray_recorder.capture('SQLAlchemy-enable_eagerloads')
    def enable_eagerloads(self, value):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().enable_eagerloads(value)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_labels')
    def with_labels(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_labels()

    @_generative()
    @xray_recorder.capture('SQLAlchemy-enable_assertions')
    def enable_assertions(self, value):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().enable_assertions(value)

    
    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_polymorphic')
    def with_polymorphic(self,
                         cls_or_mappers,
                         selectable=None,
                         polymorphic_on=None):
        return super().with_polymorphic(cls_or_mappers, selectable, polymorphic_on)
                
    @_generative()
    @xray_recorder.capture('SQLAlchemy-yield_per')
    def yield_per(self, count):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().yield_per(count)

    @xray_recorder.capture('SQLAlchemy-get')
    def get(self, ident):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().get(ident)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-correlate')
    def correlate(self, *args):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().correlate(*args)
    
    @_generative()
    @xray_recorder.capture('SQLAlchemy-autoflush')
    def autoflush(self, setting):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().autoflush(setting)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-populate_existing')
    def populate_existing(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().populate_existing()

    @xray_recorder.capture('SQLAlchemy-with_parent')
    def with_parent(self, instance, property=None, from_entity=None):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_parent(instance, property, from_entity)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-add_entity')
    def add_entity(self, entity, alias=None):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().add_entity(entity, alias)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_session')
    def with_session(self, session):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_session(session)

    @xray_recorder.capture('SQLAlchemy-from_self')
    def from_self(self, *entities):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().from_self(*entities)

    @xray_recorder.capture('SQLAlchemy-values')
    def values(self, *columns):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().values(*columns)

    @xray_recorder.capture('SQLAlchemy-value')
    def value(self, column):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().value(column)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_entities')
    def with_entities(self, *entities):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_entities(*entities)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-add_columns')
    def add_columns(self, *column):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().add_columns(*column)

    @xray_recorder.capture('SQLAlchemy-add_column')
    def add_column(self, column):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().add_column(column)

    @xray_recorder.capture('SQLAlchemy-options')
    def options(self, *args):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().options(*args)

    @xray_recorder.capture('SQLAlchemy-with_transformation')
    def with_transformation(self, fn):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_transformation(fn)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_hint')
    def with_hint(self, selectable, text, dialect_name='*'):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_hint(selectable, text, dialect_name)

    @xray_recorder.capture('SQLAlchemy-with_statement_hint')
    def with_statement_hint(self, text, dialect_name='*'):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_statement_hint(text, dialect_name)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-execution_options')
    def execution_options(self, **kwargs):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().execution_options(**kwargs)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_lockmode')
    def with_lockmode(self, mode):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().with_lockmode(mode)

    @_generative()
    @xray_recorder.capture('SQLAlchemy-with_for_update')
    def with_for_update(self, read=False, nowait=False, of=None,
                        skip_locked=False, key_share=False):
        return super().with_for_update(read, nowait, skip_locked, key_share)
                            
    @_generative()
    @xray_recorder.capture('SQLAlchemy-params')
    def params(self, *args, **kwargs):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().params(*args, **kwargs)

    @xray_recorder.capture('SQLAlchemy-filter')
    def filter(self, *criterion):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().filter(*criterion)

    @xray_recorder.capture('SQLAlchemy-filter_by')
    def filter_by(self, **kwargs):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().filter_by(**kwargs)

    @xray_recorder.capture('SQLAlchemy-order_by')
    def order_by(self, *criterion):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().order_by(*criterion)

    @xray_recorder.capture('SQLAlchemy-group_by')
    def group_by(self, *criterion):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().group_by(*criterion)

    @xray_recorder.capture('SQLAlchemy-having')
    def having(self, criterion):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().having(criterion)

    @xray_recorder.capture('SQLAlchemy-union')
    def union(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().union(*q)

    @xray_recorder.capture('SQLAlchemy-union_all')
    def union_all(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().union_all(*q)

    @xray_recorder.capture('SQLAlchemy-intersect')
    def intersect(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().intersect(*q)

    @xray_recorder.capture('SQLAlchemy-intersect_all')
    def intersect_all(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().intersect_all(*q)

    @xray_recorder.capture('SQLAlchemy-except_')
    def except_(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().except_(*q)

    @xray_recorder.capture('SQLAlchemy-except_all')
    def except_all(self, *q):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().except_all(*q)

    @xray_recorder.capture('SQLAlchemy-join')
    def join(self, *props, **kwargs):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().join(*props, **kwargs)

    @xray_recorder.capture('SQLAlchemy-outerjoin')
    def outerjoin(self, *props, **kwargs):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().outerjoin(*props, **kwargs)

    @xray_recorder.capture('SQLAlchemy-reset_joinpoint')
    def reset_joinpoint(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().reset_joinpoint()

    @xray_recorder.capture('SQLAlchemy-select_from')
    def select_from(self, *from_obj):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().select_from(*from_obj)

    @xray_recorder.capture('SQLAlchemy-select_entity_from')
    def select_entity_from(self, from_obj):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().select_entity_from(from_obj)

    @xray_recorder.capture('SQLAlchemy-slice')
    def slice(self, start, stop):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().slice(start, stop)

    @xray_recorder.capture('SQLAlchemy-limit')
    def limit(self, limit):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().limit(limit)

    @xray_recorder.capture('SQLAlchemy-offset')
    def offset(self, offset):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().offset(offset)

    @xray_recorder.capture('SQLAlchemy-distinct')
    def distinct(self, *criterion):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().distinct(*criterion)

    @xray_recorder.capture('SQLAlchemy-prefix_with')
    def prefix_with(self, *prefixes):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().prefix_with(*prefixes)

    @xray_recorder.capture('SQLAlchemy-suffix_with')
    def suffix_with(self, *suffixes):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().suffix_with(*suffixes)

    @xray_recorder.capture('SQLAlchemy-all')
    def all(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().all()

    @xray_recorder.capture('SQLAlchemy-from_statement')
    def from_statement(self, statement):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().from_statement(statement)

    @xray_recorder.capture('SQLAlchemy-first')
    def first(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().first()

    @xray_recorder.capture('SQLAlchemy-one_or_none')
    def one_or_none(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().one_or_none()

    @xray_recorder.capture('SQLAlchemy-one')
    def one(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().one()

    @xray_recorder.capture('SQLAlchemy-scalar')
    def scalar(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().scalar()

    @xray_recorder.capture('SQLAlchemy-instances')
    def instances(self, cursor, __context=None):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().instances(cursor, __context)

    @xray_recorder.capture('SQLAlchemy-merge_result')
    def merge_result(self, iterator, load=True):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().merge_result(iterator, load)

    @xray_recorder.capture('SQLAlchemy-exists')
    def exists(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().exists()

    @xray_recorder.capture('SQLAlchemy-count')
    def count(self):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().count()

    @xray_recorder.capture('SQLAlchemy-delete')
    def delete(self, synchronize_session='evaluate'):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().delete(synchronize_session)

    @xray_recorder.capture('SQLAlchemy-update')
    def update(self, values, synchronize_session='evaluate', update_args=None):
        xray_recorder.current_subsegment().put_metadata("sql", str(self));
        return super().update(values, synchronize_session, update_args)
