from google.appengine.ext import db
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.conf import settings
import pickle
import datetime
import os.path

GENDER_CHOICES = ( ('F', _('Female')), ('M', _('Male')),)
GENDER_IMAGES = { "M": "%simages/male.png" % settings.MEDIA_URL, "F": "%simages/female.png" % settings.MEDIA_URL }

class Continent(db.Model):
    code = db.StringProperty(required=True)
    name = db.StringProperty(required=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/continent/%s/" % self.slug

    class Admin:
        pass

    class Meta:
        verbose_name = _('Continent')
        verbose_name_plural = _('Continents')

class Country(db.Model):
    name = db.StringProperty(required=True)
    code = db.StringProperty(required=True)
    continent = db.ReferenceProperty(Continent)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return "/country/%s/" % self.slug

    class Admin:
        list_display = ('name', 'continent')
        list_filter = ['continent']

    class Meta:
        ordering = ['name']
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')


class Profile(db.Model):
    """
    User profile model
    """

    firstname = db.StringProperty()
    surname = db.StringProperty()
    user = db.UserProperty()
    birthdate = db.DateProperty(default=datetime.date.today())
    date = db.DateTimeProperty(auto_now_add=True)
    url = db.LinkProperty()
    about = db.TextProperty()
    geopoint = db.GeoPtProperty()
    gender = db.StringProperty()
    public = db.BlobProperty()
    country = db.ReferenceProperty(Country)
    location = db.StringProperty()

    # Avatar zone
    avatartemp = db.BlobProperty()
    avatar = db.BlobProperty()
    avatar96 = db.BlobProperty()
    avatar64 = db.BlobProperty()
    avatar32 = db.BlobProperty()
    avatar16 = db.BlobProperty()

    class Admin:
        pass

    def visible(self):
        return pickle.loads(self.public)

    def getavatar(self, size=96):
        return "/profile/getavatar/%s/" % self.user

    def __unicode__(self):
        return _("%s's profile") % self.user

    def get_genderimage_url(self):
        return GENDER_IMAGES[self.gender]

    def get_absolute_url(self):
        return "/profile/users/%s/" % self.user.nickname()

    def yearsold(self):
        return (datetime.date.today().toordinal() - self.birthdate.toordinal()) / 365

    def save(self):
        if not self.public:
            public = dict()
            for item in self.__dict__.keys() + [ 'avatar', 'nickname', 'email' ]:
                public[item] = False
            public["nickname"] = True
            public["avatar"] = True
            self.public = pickle.dumps(public)
        super(Profile, self).save()
