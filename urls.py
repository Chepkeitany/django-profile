from django.conf.urls.defaults import *
from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from userprofile.views import get_profiles, get_current_user

urlpatterns = patterns('',

    # Demo FrontPage$
    (r'^$', direct_to_template, {'extra_context': { 'user': get_current_user, 'profiles': get_profiles }, 'template': 'front.html' }),

    # Profile application
    (r'^accounts/', include('userprofile.urls')),

)
