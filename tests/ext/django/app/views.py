import sqlite3

from django.http import HttpResponse
from django.conf.urls import url
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'index.html'


def ok(request):
    return HttpResponse(status=200)


def fault(request):
    {}['key']


def call_db(request):
    conn = sqlite3.connect(':memory:')
    q = 'SELECT name FROM sqlite_master'
    conn.execute(q)
    return HttpResponse(status=201)


# def template(request):


urlpatterns = [
    url(r'^200ok/$', ok, name='200ok'),
    url(r'^500fault/$', fault, name='500fault'),
    url(r'^call_db/$', call_db, name='call_db'),
    url(r'^template/$', IndexView.as_view(), name='template'),
]
