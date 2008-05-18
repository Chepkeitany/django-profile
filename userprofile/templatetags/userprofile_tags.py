from django.template import Library
from django.template.defaultfilters import stringfilter
from google.appengine.api import users
from userprofile.models import Profile,Avatar
from django.conf import settings
import os.path

register = Library()

@register.inclusion_tag('userprofile/usercard.html')
def get_usercard(profile):
    return locals()

@register.filter
@stringfilter
def avatar(email, width):
    try:
        user = users.User(email)
        avatar = Avatar.filter("user=",user).get()
        if avatar.get_photo_filename() and os.path.isfile(avatar.get_photo_filename()):
            avatar_url = avatar.get_absolute_url()
        else:
            raise Exception()
    except:
        avatar_url = "%simages/default.gif" % settings.MEDIA_URL

    path, extension = os.path.splitext(avatar_url)
    return  "%s.%s%s" % (path, width, extension)
