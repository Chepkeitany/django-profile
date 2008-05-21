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

class AvatarForm(forms.Form):
    """
    The avatar form requires only one image field.
    """
    photo = forms.FileField()

    def clean_photo(self):
        ext_mimetypes = { 'jpg': 'image/jpeg', 'gif': 'image/gif', 'png': 'image/png', }
        photo = self.cleaned_data.get('photo')
        if not photo.filename.split(".")[-1] in ext_mimetypes:
            raise forms.ValidationError(_('The file type is invalid: %s' % type))

        return photo


class AvatarCropForm(forms.Form):
    """
    Crop dimensions form
    """
    top = forms.IntegerField()
    bottom = forms.IntegerField()
    left = forms.IntegerField()
    right = forms.IntegerField()

