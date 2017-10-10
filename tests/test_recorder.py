from .util import get_new_stubbed_recorder


xray_recorder = get_new_stubbed_recorder()
xray_recorder.configure(sampling=False)


def test_subsegment_parenting():

    segment = xray_recorder.begin_segment('name')
    subsegment = xray_recorder.begin_subsegment('name')
    xray_recorder.end_subsegment('name')
    assert xray_recorder.get_trace_entity() is segment

    subsegment1 = xray_recorder.begin_subsegment('name1')
    subsegment2 = xray_recorder.begin_subsegment('name2')

    assert subsegment2.parent_id == subsegment1.id
    assert subsegment1.parent_id == segment.id
    assert subsegment.parent_id == xray_recorder.current_segment().id

    xray_recorder.end_subsegment()
    assert not subsegment2.in_progress
    assert subsegment1.in_progress
    assert xray_recorder.current_subsegment().id == subsegment1.id

    xray_recorder.end_subsegment()
    assert not subsegment1.in_progress
    assert xray_recorder.get_trace_entity() is segment


def test_subsegments_streaming():

    segment = xray_recorder.begin_segment('name')
    for i in range(0, 50):
        xray_recorder.begin_subsegment(name=str(i))
    for i in range(0, 40):
        xray_recorder.end_subsegment()

    assert segment.get_total_subsegments_size() < 50
    assert xray_recorder.current_subsegment().name == '9'
