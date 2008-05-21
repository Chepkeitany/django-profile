from django.shortcuts import render_to_response
from google.appengine.api import users
from django.http import HttpResponseRedirect, HttpResponse
from userprofile.forms import ProfileForm, AvatarForm, AvatarCropForm
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson
from userprofile.models import Avatar, Profile, Continent, Country
from django.template import RequestContext
from google.appengine.api.urlfetch import fetch
from django.conf import settings
import random
import urllib
from xml.dom import minidom
import os

IMSIZES = ( 128, 96, 64, 32, 24, 16 )

def login_required(func):
    def _wrapper(request, *args, **kw):
        user = users.get_current_user()
        if user:
            return func(request, *args, **kw)
        else:
            return HttpResponseRedirect(users.create_login_url(request.get_full_path()))

    return _wrapper

@login_required
def fetch_geodata(request, lat, lng):
    user = users.get_current_user()
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        url = "http://ws.geonames.org/countrySubdivision?lat=%s&lng=%s" % (lat, lng)
        dom = minidom.parseString(fetch(url).content)
        country = dom.getElementsByTagName('countryCode')
        if len(country) >=1:
            country = country[0].childNodes[0].data
        region = dom.getElementsByTagName('adminName1')
        if len(region) >=1:
            region = region[0].childNodes[0].data

        country = Country.all().filter("code = ", country).get()
        return HttpResponse(simplejson.dumps({'success': True, 'country': country.key().__str__(), 'region': region}))
    else:
        raise Http404()

def public(request, APIKEY, current_user, template):
    profile = None
    for p in Profile.all():
        if p.user.nickname() == current_user:
            profile = p
            user = p.user
            break

    if not profile:
        raise Http404

    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def private(request, APIKEY, template):
    """
    Private part of the user profile
    """
    user = users.get_current_user()
    profile = Profile.all().filter("user = ", user).get()
    if not profile:
        profile = Profile(user=user)
        profile.save()

    form = ProfileForm(instance=profile)
    continents = Continent.all()
    country_data = dict()
    spain = Country.all().filter("name = ", "Spain").get()
    for continent in continents:
        country_data[continent] = Country.all().filter("continent = ", continent)

    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def save(request):
    user = users.get_current_user()
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' and request.method=="POST":
        profile = Profile.all().filter("user = ", user).get()
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponse(simplejson.dumps({'success': True}))
        else:
            return HttpResponse(simplejson.dumps({'success': False }))
    else:
        raise Http404()

@login_required
def delete(request, template):
    user = users.get_current_user()
    if request.method == "POST":
        # Remove the profile
        for profile in Profile.all().filter("user = ", user):
            profile.delete()
        for avatar in Avatar.all().filter("user = ", user):
            avatar.delete()

        return HttpResponseRedirect('%sdone/' % request.path)

    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def avatarChoose(request, template):
    """
    Avatar choose
    """
    user = users.get_current_user()
    if not request.method == "POST":
        form = AvatarForm()
    else:
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            for avatar in Avatar.all().filter("user = ", user).filter("valid = ", False):
                avatar.delete()

            photo = form.cleaned_data.get('photo')
            ext_mimetypes = { 'jpg': 'image/jpeg', 'gif': 'image/gif', 'png': 'image/png' }
            mimetype = ext_mimetypes.get(photo.filename.split(".")[-1])
            avatar= Avatar(photo=photo.content, mimetype=mimetype, user=user)
            avatar.save()

    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def avatarCrop(request, avatar_id, template):
    """
    Avatar management
    """
    user = users.get_current_user()
    if not request.method == "POST":
        raise Http404()

    form = AvatarCropForm(request.POST)
    if form.is_valid():
        avatar = Avatar.all().filter("user = ", request.user).filter("pk = ", avatar_id).get()
        avatar.valid = True
        top = int(request.POST.get('top'))
        left = int(request.POST.get('left'))
        right = int(request.POST.get('right'))
        bottom = int(request.POST.get('bottom'))
        if top < 0: top = 0
        if left < 0: left = 0
        avatar.box = "%s-%s-%s-%s" % ( int(left), int(top), int(right), int(bottom))
        avatar.save()
        done = True

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def getavatar(request, avatar_id, size=None):
    try:
        Avatar.all().filter("id = ", id).get()
    except:
        return HttpResponseRedirect("/static/images/default.png")

@login_required
def avatarDelete(request, avatar_id=False):
    user = users.get_current_user()
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        try:
            avatar = Avatar.all().filter("user = ", user).get()
            avatar.delete()
        except:
            pass
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
        raise Http404()
