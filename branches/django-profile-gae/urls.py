from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from userprofile.models import Profile

urlpatterns = patterns('',
    # Demo FrontPage
    (r'^$', direct_to_template, {'extra_context': { 'profiles': Profile.all() }, 'template': 'front.html' }),

    # Profile application
    (r'^profile/', include('userprofile.urls')),

)
