from django.shortcuts import render_to_response
from google.appengine.api import users
from django.http import HttpResponseRedirect, HttpResponse
from userprofile.forms import ProfileForm, AvatarForm, AvatarCropForm
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson
from userprofile.models import Avatar, Profile, Continent, Country
from django.template import RequestContext
from django.conf import settings
import random
import urllib
from xml.dom import minidom
import os

IMSIZES = ( 128, 96, 64, 32, 24, 16 )

def fetch_geodata(request, lat, lng):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        url = "http://ws.geonames.org/countrySubdivision?lat=%s&lng=%s" % (lat, lng)
        dom = minidom.parse(urllib.urlopen(url))
        country = dom.getElementsByTagName('countryCode')
        if len(country) >=1:
            country = country[0].childNodes[0].data
        region = dom.getElementsByTagName('adminName1')
        if len(region) >=1:
            region = region[0].childNodes[0].data

        return HttpResponse(simplejson.dumps({'success': True, 'country': country, 'region': region}))
    else:
        raise Http404()

def public(request, APIKEY, current_user, template):
    try:
        profile = User.objects.get(username=current_user, is_active=True).get_profile()
    except:
        raise Http404

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def private(request, APIKEY, template):
    """
    Private part of the user profile
    """
    user = users.get_current_user()

    if settings.DEBUG:
        user = users.User("david.rubert@gmail.com")

    if not user: users.create_login_url(request.path)

    profile = Profile.all().filter("user=", user).get()
    if not profile:
        profile = Profile(user=user)
        profile.save()

    if request.method == "POST" and form.is_valid():
        form = ProfileForm(request.POST, instance=profile)
    else:
        form = ProfileForm(instance=profile)

    continents = Continent.all()
    country_data = dict()
    for continent in continents:
        country_data[continent] = Country.all().filter(continent=continent)

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def save(request):
    user = users.get_current_user()

    if settings.DEBUG:
        user = users.User("david.rubert@gmail.com")

    if not user: users.create_login_url(request.path)

    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' and request.method=="POST":
        profile = Profile.all().filter("user=", user).get()
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponse(simplejson.dumps({'success': True}))
        else:
            return HttpResponse(simplejson.dumps({'success': False }))
    else:
        raise Http404()

def delete(request, template):
    user = users.get_current_user()

    if settings.DEBUG:
        user = users.User("david.rubert@gmail.com")

    if not user: users.create_login_url(request.path)

    if request.method == "POST":
        # Remove the profile
        try:
            Profile.all().filter("user=", user).delete()
        except:
            pass

        # Remove the avatar if exists
        try:
            Avatar.all().filter("user=", user).delete()
        except:
            pass

        return HttpResponseRedirect('%sdone/' % request.path)

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def avatarChoose(request, template):
    """
    Avatar choose
    """
    if not request.method == "POST":
        form = AvatarForm()
    else:
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data.get('photo')
            Avatar.objects.filter(user=request.user, valid=False).delete()
            avatar = Avatar(user=request.user)
            avatar.save_photo_file("%s%s" % (request.user.username, data.get('extension')), data['photo'].content)
            avatar.save()

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def avatarCrop(request, avatar_id, template):
    """
    Avatar management
    """
    if not request.method == "POST":
        raise Http404()

    form = AvatarCropForm(request.POST)
    if form.is_valid():
        avatar = Avatar.objects.get(user = request.user, pk = avatar_id)
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

def avatarDelete(request, avatar_id=False):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        try:
            avatar = Avatar.objects.get(user=request.user)
            avatar.delete()
        except:
            pass
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
        raise Http404()
