from django.template import Library
from django.template.defaultfilters import stringfilter
from google.appengine.api import users
from userprofile.models import Profile
from django.conf import settings
import os.path

register = Library()

@register.inclusion_tag('userprofile/usercard.html')
def get_usercard(profile):
    return locals()
