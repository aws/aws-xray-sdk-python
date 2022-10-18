import sqlite3

from django.http import HttpResponse
from django.urls import path
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'index.html'


class TemplateBlockView(TemplateView):
    template_name = 'block_user.html'


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
    path('200ok/', ok, name='200ok'),
    path('500fault/', fault, name='500fault'),
    path('call_db/', call_db, name='call_db'),
    path('template/', IndexView.as_view(), name='template'),
    path('template_block/', TemplateBlockView.as_view(), name='template_block'),
]
