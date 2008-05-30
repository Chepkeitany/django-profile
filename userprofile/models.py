from google.appengine.ext import db
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext as _
from django.conf import settings
import pickle
import datetime
import os.path

AVATARSIZES = ( 128, 96, 64, 32, 16 )
GENDER_CHOICES = ( ('F', _('Female')), ('M', _('Male')),)
GENDER_IMAGES = { "M": "%simages/male.png" % settings.MEDIA_URL, "F": "%simages/female.png" % settings.MEDIA_URL }

class Continent(db.Model):
    """
    Continent class. Simple class with the information about continents.
    It can be filled up with this data:

Continent(name="Asia", code="AS").save()
Continent(name="Africa", code="AF").save()
Continent(name="Europe", code="EU").save()
Continent(name="North America", code="NA").save()
Continent(name="South America", code="SA").save()
Continent(name="Oceania", code="OC").save()
Continent(name="Antarctica", code="AN").save()
    """
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
    """
    Country class with the countries data needed in the Profile class. Dependent
    of the Continent class.

    Fill the database with this code:

f = open("db/countries.txt")
for line in f.xreadlines():
    line = line.strip()
    d, name = line.split('"')[:-1]
    continent, code = d.split(",")[:-1]
    c = Continent.all().filter("code = ", continent).get()
    p = Country(name=name, code=code, continent=c)
    p.save()

    """
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
    visibility = db.BlobProperty()

    class Admin:
        pass

    def visible(self):
        return pickle.loads(self.public)

    def avatar(self, size=96):
        return "/profile/avatar/%s" % self.user

    def __unicode__(self):
        return _("%s's profile") % self.user

    def get_genderimage_url(self):
        return GENDER_IMAGES[self.gender]

    def get_absolute_url(self):
        return "/profile/users/%s/" % self.user.nickname()

    def yearsold(self):
        return (datetime.date.today().toordinal() - self.birthdate.toordinal()) / 365

class Avatar(db.Model):
    """
    Avatar class. Every user can have one avatar associated.
    """
    photo = db.BlobProperty()
    photo96 = db.BlobProperty()
    photo64 = db.BlobProperty()
    photo32 = db.BlobProperty()
    photo16 = db.BlobProperty()
    mimetype = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    box = db.StringProperty()
    profile = db.ReferenceProperty(Profile)
    valid = db.BooleanProperty(default=False)

    def get_absolute_url(self):
        return "/profile/avatarkey/%s/" % self.key().__str__()

    def __unicode__(self):
        return "%s-%s" % (self.user, self.photo)

    class Admin:
        pass
