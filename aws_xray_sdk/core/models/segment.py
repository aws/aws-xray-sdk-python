import copy

from .entity import Entity
from .traceid import TraceId
from ..utils.atomic_counter import AtomicCounter
from ..exceptions.exceptions import SegmentNameMissingException


class Segment(Entity):
    """
    The compute resources running your application logic send data
    about their work as segments. A segment provides the resource's name,
    details about the request, and details about the work done.
    """
    def __init__(self, name, entityid=None, traceid=None,
                 parent_id=None, sampled=True):
        """
        Create a segment object.

        :param str name: segment name. If not specified a
            SegmentNameMissingException will be thrown.
        :param str entityid: hexdigits segment id.
        :param str traceid: The trace id of the segment.
        :param str parent_id: The parent id of the segment. It comes
            from id of an upstream segment or subsegment.
        :param bool sampled: If False this segment will not be sent
            to the X-Ray daemon.
        """
        if not name:
            raise SegmentNameMissingException("Segment name is required.")

        super(Segment, self).__init__(name)

        if not traceid:
            traceid = TraceId().to_id()
        self.trace_id = traceid
        if entityid:
            self.id = entityid

        self.in_progress = True
        self.sampled = sampled
        self.ref_counter = AtomicCounter()
        self._subsegments_counter = AtomicCounter()

        if parent_id:
            self.parent_id = parent_id

    def add_subsegment(self, subsegment):
        """
        Add input subsegment as a child subsegment and increment
        reference counter and total subsegments counter.
        """
        super(Segment, self).add_subsegment(subsegment)
        self.increment()

    def increment(self):
        """
        Increment reference counter to track on open subsegments
        and total subsegments counter to track total size of subsegments
        it currently hold.
        """
        self.ref_counter.increment()
        self._subsegments_counter.increment()

    def decrement_ref_counter(self):
        """
        Decrement reference counter by 1 when a subsegment is closed.
        """
        self.ref_counter.decrement()

    def ready_to_send(self):
        """
        Return True if the segment doesn't have any open subsegments
        and itself is not in progress.
        """
        return self.ref_counter.get_current() <= 0 and not self.in_progress

    def get_total_subsegments_size(self):
        """
        Return the number of total subsegments regardless of open or closed.
        """
        return self._subsegments_counter.get_current()

    def decrement_subsegments_size(self):
        """
        Decrement total subsegments by 1. This usually happens when
        a subsegment is streamed out.
        """
        return self._subsegments_counter.decrement()

    def remove_subsegment(self, subsegment):
        """
        Remove the reference of input subsegment.
        """
        super(Segment, self).remove_subsegment(subsegment)
        self.decrement_subsegments_size()

    def __getstate__(self):
        """
        Used by jsonpikle to remove unwanted fields.
        """
        properties = copy.copy(self.__dict__)
        super(Segment, self)._delete_empty_properties(properties)

        del properties['ref_counter']
        del properties['_subsegments_counter']
        return properties
