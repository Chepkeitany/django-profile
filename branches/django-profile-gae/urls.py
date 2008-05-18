from django.conf.urls.defaults import *
from google.appengine.api import users
from django.views.generic.simple import direct_to_template
from userprofile.models import Profile

urlpatterns = patterns('',
    # Demo FrontPage
    (r'^$', direct_to_template, {'extra_context': { 'user': users.get_current_user(), 'profiles': Profile.all() }, 'template': 'front.html' }),

    # Profile application
    (r'^profile/', include('userprofile.urls')),

)
