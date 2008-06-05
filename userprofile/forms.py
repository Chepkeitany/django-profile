from google.appengine.ext.db import djangoforms
from django import newforms as forms
from django.utils.translation import ugettext as _
from django.conf import settings
from userprofile.models import Profile

class ProfileForm(djangoforms.ModelForm):
    """
    Profile Form. Composed by all the Profile model fields.
    """

    class Meta:
        model = Profile
        exclude = ('user', 'slug', 'date', 'avtemp', 'avatar', 'avatar16', 'avatar32', 'avatar64', 'avatar96')

class AvatarForm(forms.Form):
    """
    The avatar form requires only one image field.
    """
    photo = forms.FileField(required=False)
    url = forms.URLField(required=False)

    def clean_photo(self):
        photo = self.cleaned_data['photo']
        if photo and not photo.filename.split(".")[-1].lower() in settings.MIMETYPES.keys():
            raise forms.ValidationError(_('The file type is invalid: %s' % type))

        return photo
    
    def clean_url(self):
        url = self.cleaned_data['url']
        return url

    def clean(self):
        if not (self.cleaned_data.get('photo') or self.cleaned_data.get('url') or self.cleaned_data.get('flickr')):
            raise forms.ValidationError(_('You must enter one of the 3 possible options'))
        else:
            return self.cleaned_data


class AvatarCropForm(forms.Form):
    """
    Crop dimensions form
    """
    top = forms.IntegerField()
    bottom = forms.IntegerField()
    left = forms.IntegerField()
    right = forms.IntegerField()

