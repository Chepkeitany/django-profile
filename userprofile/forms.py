from django import newforms as forms
from google.appengine.ext.db import djangoforms
from django.core.exceptions import ObjectDoesNotExist
from userprofile.models import Profile, Avatar, GENDER_CHOICES
from django.utils.translation import ugettext as _
from userprofile.models import Country

class ProfileForm(djangoforms.ModelForm):
    """
    Profile Form. Composed by all the Profile model fields.
    """

    class Meta:
        model = Profile
        exclude = ('user', 'slug', 'date')

class AvatarForm(djangoforms.ModelForm):
    """
    The avatar form requires only one image field.
    """
    class Meta:
        model = Avatar
        exclude = ('user', 'date', 'valid', 'box')

class AvatarCropForm(forms.Form):
    """
    Crop dimensions form
    """
    top = forms.IntegerField()
    bottom = forms.IntegerField()
    left = forms.IntegerField()
    right = forms.IntegerField()

