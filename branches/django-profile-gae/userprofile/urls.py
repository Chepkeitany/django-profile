from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from userprofile.views import *
from django.conf import settings

APIKEY = hasattr(settings, "APIKEY") and settings.APIKEY or None
WEBSEARCH = hasattr(settings, "WEBSEARCH") and settings.WEBSEARCH or None

urlpatterns = patterns('',
    # Private profile
    (r'^profile/$', overview, { 'section': 'overview', 'APIKEY': APIKEY, 'template': 'userprofile/overview.html'}),
    (r'^profile/edit/(?P<section>location)/$', profile, {'APIKEY': APIKEY, 'template': 'userprofile/location.html'}),
    (r'^profile/edit/(?P<section>personal)/$', profile, {'template': 'userprofile/personal.html'}),
    (r'^profile/edit/(?P<section>personal|location|public)/done/$', direct_to_template, { 'extra_context': { 'user': get_current_user }, 'template': 'userprofile/profile_done.html'}),
    (r'^profile/delete/$', delete, { 'section': 'delete', 'template': 'userprofile/delete.html'}),
    (r'^profile/delete/done/$', direct_to_template, { 'extra_context': { 'user': get_current_user }, 'section': 'delete', 'template': 'userprofile/delete_done.html'}),
    (r'^profile/edit/public/$', makepublic, { 'section': 'makepublic', 'APIKEY': APIKEY, 'template': 'userprofile/makepublic.html'}),
    (r'^profile/edit/avatar/$', avatarchoose, { 'section': 'avatar', 'websearch': WEBSEARCH, 'template': 'userprofile/avatar_choose.html'}),
    (r'^profile/edit/avatar/delete/$', avatardelete),
    (r'^profile/edit/avatar/search/$', searchimages, { 'section': 'avatar', 'template': 'userprofile/avatar_search.html'}),
    (r'^profile/edit/avatar/crop/$', avatarcrop, { 'section': 'avatar', 'template': 'userprofile/avatar_crop.html'}),
    (r'^profile/edit/avatar/crop/done/$', direct_to_template, { 'section': 'avatar', 'template': 'userprofile/avatar_done.html'}),
    (r'^profile/getcountry_info/(?P<lat>[0-9\.\-]+)/(?P<lng>[0-9\.\-]+)/$', fetch_geodata),

    # Public profile
    (r'^profile/(?P<current_user>[a-zA-Z0-9\-_]*)/$', public, {'APIKEY': APIKEY, 'template': 'userprofile/public.html'}),
)
