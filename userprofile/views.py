from django.shortcuts import render_to_response
from userprofile import flickr
from google.appengine.api import users
from google.appengine.api import images, urlfetch
from google.appengine.ext.db import get
from django.http import HttpResponseRedirect, HttpResponse
from userprofile.forms import ProfileForm, AvatarForm, AvatarCropForm
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist
import pickle
from django.utils import simplejson
from userprofile.models import Avatar, Profile, Continent, Country
from django.template import RequestContext
from google.appengine.api.urlfetch import fetch
from django.conf import settings
import random
import urllib
from xml.dom import minidom
import os

flickr.API_KEY=settings.FLICKR_APIKEY

def login_required(func):
    def _wrapper(request, *args, **kw):
        user = users.get_current_user()
        if user:
            return func(request, *args, **kw)
        else:
            return HttpResponseRedirect(users.create_login_url(request.get_full_path()))

    return _wrapper

@login_required
def logout(request):
    user = users.get_current_user()
    return HttpResponseRedirect(users.create_logout_url("/"))

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
    user = users.get_current_user()
    for p in Profile.all():
        if p.user.nickname() == current_user:
            profile = p
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
        form = ProfileForm(data=request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            if not form.cleaned_data.get("country"):
                profile.country = None
                profile.location = None
                profile.geopoint = None

            public = dict()
            for item in profile.__dict__.get("_entity").keys() + [ 'avatar', 'nickname', 'email' ]:
                if request.POST.has_key("%s_public" % item):
                    public[item] = request.POST.get("%s_public" % item)

            profile.public = pickle.dumps(public)
            profile.save()

            return HttpResponse(simplejson.dumps({ 'success': True }))
        else:
            return HttpResponse(simplejson.dumps({ 'success': False }))
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
def searchflickr(request, template):
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' and request.method=="POST" and request.POST.get('search'):
        photos = flickr.photos_search(tags=request.POST.get('search'))
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
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
        profile = Profile.all().filter("user = ", user).get()
        form = AvatarForm(request.POST, request.FILES)
        if form.is_valid():
            for avatar in Avatar.all().filter("user = ", user).filter("valid = ", False):
                avatar.delete()

            photo = form.cleaned_data.get('photo')
            url = form.cleaned_data.get('url')
            if url:
                photo = urlfetch.fetch(url)

            avatar= Avatar(photo=photo.content, mimetype='image/png', profile=profile)
            avatar.save()


    return render_to_response(template, locals(), context_instance=RequestContext(request))

@login_required
def avatarCrop(request, key, template):
    """
    Avatar management
    """
    user = users.get_current_user()
    profile = Profile.all().filter("user = ", user).get()
    if not request.method == "POST":
        raise Http404()

    form = AvatarCropForm(request.POST)
    if form.is_valid():
        for avatar in Avatar.all().filter("profile = ", profile):
            avatar.valid = False
            avatar.save()

        avatar = get(key)
        avatar.valid = True
        top = int(request.POST.get('top'))
        left = int(request.POST.get('left'))
        right = int(request.POST.get('right'))
        bottom = int(request.POST.get('bottom'))
        width = int(request.POST.get('width'))
        height = int(request.POST.get('height'))
        if top < 0: top = 0
        if left < 0: left = 0
        avatar.box = "%s-%s-%s-%s" % ( float(left), float(top), float(right), float(bottom))
        avatar.photo = images.crop(avatar.photo, float(left)/width, float(top)/height, float(right)/width, float(bottom)/height)
        avatar.photo96 = images.resize(avatar.photo, 96)
        avatar.photo64 = images.resize(avatar.photo, 64)
        avatar.photo32 = images.resize(avatar.photo, 32)
        avatar.photo16 = images.resize(avatar.photo, 16)
        avatar.save()
        done = True

        for avatar in Avatar.all().filter("profile = ", profile).filter("valid = ", False):
            avatar.delete()

    return render_to_response(template, locals(), context_instance=RequestContext(request))

def getavatar(request, current_user=None, key=None, size=96):
    if current_user:
        profile = None
        for p in Profile.all():
            if p.user.nickname() == current_user:
                profile = p
                current_user = p.user
                break

        if profile:
            avatar = Avatar.all().filter("profile = ", p).filter("valid = ", True).get()
            if avatar:
                return HttpResponse(getattr(avatar, "photo%s" % size), mimetype=avatar.mimetype)
            else:
                return HttpResponseRedirect("%simages/default.png" % settings.MEDIA_URL)
        else:
            raise Http404

    elif key:
        avatar = get(key)
        if avatar:
            return HttpResponse(avatar.photo, mimetype=avatar.mimetype)
        else:
            return HttpResponseRedirect("%simages/default.png")

@login_required
def avatarDelete(request, key=False):
    user = users.get_current_user()
    profile = Profile.all().filter("user = ", user).get()
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
        if key:
            avatar = get(key)
            avatar.delete()
        else:
            try:
                for avatar in Avatar.all().filter("profile = ", profile):
                    avatar.delete()
            except:
                pass
        return HttpResponse(simplejson.dumps({'success': True}))
    else:
        raise Http404()

@login_required
def fill(request, model):
    if not users.is_current_user_admin():
        return HttpResponseRedirect("/")

    if model == "continent":
        Continent(name="Asia", code="AS").save()
        Continent(name="Africa", code="AF").save()
        Continent(name="Europe", code="EU").save()
        Continent(name="North America", code="NA").save()
        Continent(name="South America", code="SA").save()
        Continent(name="Oceania", code="OC").save()
        Continent(name="Antarctica", code="AN").save()
        return HttpResponse("ok.")
    elif model == "country":
        continents = dict()
        [ continents.setdefault(continent.code, continent) for continent in Continent.all() ]
        Country(name="Angola", code="AO", continent=continents["AF"]).save()
        Country(name="Burkina Faso", code="BF", continent=continents["AF"]).save()
        Country(name="Burundi", code="BI", continent=continents["AF"]).save()
        Country(name="Benin", code="BJ", continent=continents["AF"]).save()
        Country(name="Bouvet Island", code="BV", continent=continents["AF"]).save()
        Country(name="Botswana", code="BW", continent=continents["AF"]).save()
        Country(name="Congo, The Democratic Republic of the", code="CD", continent=continents["AF"]).save()
        Country(name="Central African Republic", code="CF", continent=continents["AF"]).save()
        Country(name="Congo", code="CG", continent=continents["AF"]).save()
        Country(name="Cote d'Ivoire", code="CI", continent=continents["AF"]).save()
        Country(name="Cameroon", code="CM", continent=continents["AF"]).save()
        Country(name="Cape Verde", code="CV", continent=continents["AF"]).save()
        Country(name="Djibouti", code="DJ", continent=continents["AF"]).save()
        Country(name="Algeria", code="DZ", continent=continents["AF"]).save()
        Country(name="Egypt", code="EG", continent=continents["AF"]).save()
        Country(name="Western Sahara", code="EH", continent=continents["AF"]).save()
        Country(name="Eritrea", code="ER", continent=continents["AF"]).save()
        Country(name="Ethiopia", code="ET", continent=continents["AF"]).save()
        Country(name="Ghana", code="GH", continent=continents["AF"]).save()
        Country(name="Gambia", code="GM", continent=continents["AF"]).save()
        Country(name="Guinea", code="GN", continent=continents["AF"]).save()
        Country(name="Equatorial Guinea", code="GQ", continent=continents["AF"]).save()
        Country(name="Guinea-Bissau", code="GW", continent=continents["AF"]).save()
        Country(name="Heard Island and McDonald Islands", code="HM", continent=continents["AF"]).save()
        Country(name="Kenya", code="KE", continent=continents["AF"]).save()
        Country(name="Comoros", code="KM", continent=continents["AF"]).save()
        Country(name="Liberia", code="LR", continent=continents["AF"]).save()
        Country(name="Lesotho", code="LS", continent=continents["AF"]).save()
        Country(name="Libyan Arab Jamahiriya", code="LY", continent=continents["AF"]).save()
        Country(name="Morocco", code="MA", continent=continents["AF"]).save()
        Country(name="Madagascar", code="MG", continent=continents["AF"]).save()
        Country(name="Mali", code="ML", continent=continents["AF"]).save()
        Country(name="Mauritania", code="MR", continent=continents["AF"]).save()
        Country(name="Mauritius", code="MU", continent=continents["AF"]).save()
        Country(name="Malawi", code="MW", continent=continents["AF"]).save()
        Country(name="Mozambique", code="MZ", continent=continents["AF"]).save()
        Country(name="Namibia", code="NA", continent=continents["AF"]).save()
        Country(name="Niger", code="NE", continent=continents["AF"]).save()
        Country(name="Nigeria", code="NG", continent=continents["AF"]).save()
        Country(name="Reunion", code="RE", continent=continents["AF"]).save()
        Country(name="Rwanda", code="RW", continent=continents["AF"]).save()
        Country(name="Seychelles", code="SC", continent=continents["AF"]).save()
        Country(name="Sudan", code="SD", continent=continents["AF"]).save()
        Country(name="Saint Helena", code="SH", continent=continents["AF"]).save()
        Country(name="Sierra Leone", code="SL", continent=continents["AF"]).save()
        Country(name="Senegal", code="SN", continent=continents["AF"]).save()
        Country(name="Somalia", code="SO", continent=continents["AF"]).save()
        Country(name="Sao Tome and Principe", code="ST", continent=continents["AF"]).save()
        Country(name="Swaziland", code="SZ", continent=continents["AF"]).save()
        Country(name="Chad", code="TD", continent=continents["AF"]).save()
        Country(name="French Southern Territories", code="TF", continent=continents["AF"]).save()
        Country(name="Togo", code="TG", continent=continents["AF"]).save()
        Country(name="Tunisia", code="TN", continent=continents["AF"]).save()
        Country(name="Tanzania, United Republic of", code="TZ", continent=continents["AF"]).save()
        Country(name="Uganda", code="UG", continent=continents["AF"]).save()
        Country(name="Mayotte", code="YT", continent=continents["AF"]).save()
        Country(name="Zambia", code="ZM", continent=continents["AF"]).save()
        Country(name="Antarctica", code="AQ", continent=continents["AN"]).save()
        Country(name="United Arab Emirates", code="AE", continent=continents["AS"]).save()
        Country(name="Afghanistan", code="AF", continent=continents["AS"]).save()
        Country(name="Armenia", code="AM", continent=continents["AS"]).save()
        Country(name="Asia/Pacific Region", code="AP", continent=continents["AS"]).save()
        Country(name="Turkey", code="TR", continent=continents["AS"]).save()
        Country(name="Azerbaijan", code="AZ", continent=continents["AS"]).save()
        Country(name="Bangladesh", code="BD", continent=continents["AS"]).save()
        Country(name="Bahrain", code="BH", continent=continents["AS"]).save()
        Country(name="Brunei Darussalam", code="BN", continent=continents["AS"]).save()
        Country(name="Bhutan", code="BT", continent=continents["AS"]).save()
        Country(name="Cocos (Keeling) Islands", code="CC", continent=continents["AS"]).save()
        Country(name="China", code="CN", continent=continents["AS"]).save()
        Country(name="Christmas Island", code="CX", continent=continents["AS"]).save()
        Country(name="Cyprus", code="CY", continent=continents["AS"]).save()
        Country(name="Georgia", code="GE", continent=continents["AS"]).save()
        Country(name="Hong Kong", code="HK", continent=continents["AS"]).save()
        Country(name="Indonesia", code="ID", continent=continents["AS"]).save()
        Country(name="Israel", code="IL", continent=continents["AS"]).save()
        Country(name="India", code="IN", continent=continents["AS"]).save()
        Country(name="British Indian Ocean Territory", code="IO", continent=continents["AS"]).save()
        Country(name="Iraq", code="IQ", continent=continents["AS"]).save()
        Country(name="Iran, Islamic Republic of", code="IR", continent=continents["AS"]).save()
        Country(name="Jordan", code="JO", continent=continents["AS"]).save()
        Country(name="Japan", code="JP", continent=continents["AS"]).save()
        Country(name="Kyrgyzstan", code="KG", continent=continents["AS"]).save()
        Country(name="Cambodia", code="KH", continent=continents["AS"]).save()
        Country(name="Korea, Democratic People's Republic of", code="KP", continent=continents["AS"]).save()
        Country(name="Korea, Republic of", code="KR", continent=continents["AS"]).save()
        Country(name="Kuwait", code="KW", continent=continents["AS"]).save()
        Country(name="Kazakhstan", code="KZ", continent=continents["AS"]).save()
        Country(name="Lao People's Democratic Republic", code="LA", continent=continents["AS"]).save()
        Country(name="Lebanon", code="LB", continent=continents["AS"]).save()
        Country(name="Sri Lanka", code="LK", continent=continents["AS"]).save()
        Country(name="Myanmar", code="MM", continent=continents["AS"]).save()
        Country(name="Mongolia", code="MN", continent=continents["AS"]).save()
        Country(name="Macao", code="MO", continent=continents["AS"]).save()
        Country(name="Maldives", code="MV", continent=continents["AS"]).save()
        Country(name="Malaysia", code="MY", continent=continents["AS"]).save()
        Country(name="Nepal", code="NP", continent=continents["AS"]).save()
        Country(name="Oman", code="OM", continent=continents["AS"]).save()
        Country(name="Philippines", code="PH", continent=continents["AS"]).save()
        Country(name="Pakistan", code="PK", continent=continents["AS"]).save()
        Country(name="Palestinian Territory", code="PS", continent=continents["AS"]).save()
        Country(name="Qatar", code="QA", continent=continents["AS"]).save()
        Country(name="Russian Federation", code="RU", continent=continents["AS"]).save()
        Country(name="Saudi Arabia", code="SA", continent=continents["AS"]).save()
        Country(name="Singapore", code="SG", continent=continents["AS"]).save()
        Country(name="Syrian Arab Republic", code="SY", continent=continents["AS"]).save()
        Country(name="Thailand", code="TH", continent=continents["AS"]).save()
        Country(name="Tajikistan", code="TJ", continent=continents["AS"]).save()
        Country(name="Turkmenistan", code="TM", continent=continents["AS"]).save()
        Country(name="Taiwan", code="TW", continent=continents["AS"]).save()
        Country(name="Uzbekistan", code="UZ", continent=continents["AS"]).save()
        Country(name="Vietnam", code="VN", continent=continents["AS"]).save()
        Country(name="Yemen", code="YE", continent=continents["AS"]).save()
        Country(name="Andorra", code="AD", continent=continents["EU"]).save()
        Country(name="Gabon", code="GA", continent=continents["AF"]).save()
        Country(name="South Africa", code="ZA", continent=continents["AF"]).save()
        Country(name="Albania", code="AL", continent=continents["EU"]).save()
        Country(name="Austria", code="AT", continent=continents["EU"]).save()
        Country(name="Bosnia and Herzegovina", code="BA", continent=continents["EU"]).save()
        Country(name="Belgium", code="BE", continent=continents["EU"]).save()
        Country(name="Bulgaria", code="BG", continent=continents["EU"]).save()
        Country(name="Belarus", code="BY", continent=continents["EU"]).save()
        Country(name="Switzerland", code="CH", continent=continents["EU"]).save()
        Country(name="Czech Republic", code="CZ", continent=continents["EU"]).save()
        Country(name="Germany", code="DE", continent=continents["EU"]).save()
        Country(name="Denmark", code="DK", continent=continents["EU"]).save()
        Country(name="Estonia", code="EE", continent=continents["EU"]).save()
        Country(name="Spain", code="ES", continent=continents["EU"]).save()
        Country(name="Europe", code="EU", continent=continents["EU"]).save()
        Country(name="Finland", code="FI", continent=continents["EU"]).save()
        Country(name="Faroe Islands", code="FO", continent=continents["EU"]).save()
        Country(name="France", code="FR", continent=continents["EU"]).save()
        Country(name="United Kingdom", code="GB", continent=continents["EU"]).save()
        Country(name="Gibraltar", code="GI", continent=continents["EU"]).save()
        Country(name="Greece", code="GR", continent=continents["EU"]).save()
        Country(name="Croatia", code="HR", continent=continents["EU"]).save()
        Country(name="Hungary", code="HU", continent=continents["EU"]).save()
        Country(name="Ireland", code="IE", continent=continents["EU"]).save()
        Country(name="Iceland", code="IS", continent=continents["EU"]).save()
        Country(name="Italy", code="IT", continent=continents["EU"]).save()
        Country(name="Liechtenstein", code="LI", continent=continents["EU"]).save()
        Country(name="Lithuania", code="LT", continent=continents["EU"]).save()
        Country(name="Luxembourg", code="LU", continent=continents["EU"]).save()
        Country(name="Latvia", code="LV", continent=continents["EU"]).save()
        Country(name="Monaco", code="MC", continent=continents["EU"]).save()
        Country(name="Moldova, Republic of", code="MD", continent=continents["EU"]).save()
        Country(name="Macedonia", code="MK", continent=continents["EU"]).save()
        Country(name="Malta", code="MT", continent=continents["EU"]).save()
        Country(name="Netherlands", code="NL", continent=continents["EU"]).save()
        Country(name="Norway", code="NO", continent=continents["EU"]).save()
        Country(name="Poland", code="PL", continent=continents["EU"]).save()
        Country(name="Portugal", code="PT", continent=continents["EU"]).save()
        Country(name="Romania", code="RO", continent=continents["EU"]).save()
        Country(name="Sweden", code="SE", continent=continents["EU"]).save()
        Country(name="Slovenia", code="SI", continent=continents["EU"]).save()
        Country(name="Svalbard and Jan Mayen", code="SJ", continent=continents["EU"]).save()
        Country(name="Slovakia", code="SK", continent=continents["EU"]).save()
        Country(name="San Marino", code="SM", continent=continents["EU"]).save()
        Country(name="Ukraine", code="UA", continent=continents["EU"]).save()
        Country(name="Holy See (Vatican City State)", code="VA", continent=continents["EU"]).save()
        Country(name="Canada", code="CA", continent=continents["NA"]).save()
        Country(name="Mexico", code="MX", continent=continents["NA"]).save()
        Country(name="United States", code="US", continent=continents["NA"]).save()
        Country(name="American Samoa", code="AS", continent=continents["OC"]).save()
        Country(name="Australia", code="AU", continent=continents["OC"]).save()
        Country(name="Cook Islands", code="CK", continent=continents["OC"]).save()
        Country(name="Fiji", code="FJ", continent=continents["OC"]).save()
        Country(name="Micronesia, Federated States of", code="FM", continent=continents["OC"]).save()
        Country(name="Guam", code="GU", continent=continents["OC"]).save()
        Country(name="Kiribati", code="KI", continent=continents["OC"]).save()
        Country(name="Marshall Islands", code="MH", continent=continents["OC"]).save()
        Country(name="Northern Mariana Islands", code="MP", continent=continents["OC"]).save()
        Country(name="New Caledonia", code="NC", continent=continents["OC"]).save()
        Country(name="Norfolk Island", code="NF", continent=continents["OC"]).save()
        Country(name="Nauru", code="NR", continent=continents["OC"]).save()
        Country(name="Niue", code="NU", continent=continents["OC"]).save()
        Country(name="New Zealand", code="NZ", continent=continents["OC"]).save()
        Country(name="French Polynesia", code="PF", continent=continents["OC"]).save()
        Country(name="Papua New Guinea", code="PG", continent=continents["OC"]).save()
        Country(name="Pitcairn", code="PN", continent=continents["OC"]).save()
        Country(name="Palau", code="PW", continent=continents["OC"]).save()
        Country(name="Solomon Islands", code="SB", continent=continents["OC"]).save()
        Country(name="Tokelau", code="TK", continent=continents["OC"]).save()
        Country(name="Tonga", code="TO", continent=continents["OC"]).save()
        Country(name="Tuvalu", code="TV", continent=continents["OC"]).save()
        Country(name="United States Minor Outlying Islands", code="UM", continent=continents["OC"]).save()
        Country(name="Vanuatu", code="VU", continent=continents["OC"]).save()
        Country(name="Wallis and Futuna", code="WF", continent=continents["OC"]).save()
        Country(name="Samoa", code="WS", continent=continents["OC"]).save()
        Country(name="Antigua and Barbuda", code="AG", continent=continents["SA"]).save()
        Country(name="Anguilla", code="AI", continent=continents["SA"]).save()
        Country(name="Netherlands Antilles", code="AN", continent=continents["SA"]).save()
        Country(name="Argentina", code="AR", continent=continents["SA"]).save()
        Country(name="Aruba", code="AW", continent=continents["SA"]).save()
        Country(name="Barbados", code="BB", continent=continents["SA"]).save()
        Country(name="Bermuda", code="BM", continent=continents["SA"]).save()
        Country(name="Bolivia", code="BO", continent=continents["SA"]).save()
        Country(name="Brazil", code="BR", continent=continents["SA"]).save()
        Country(name="Bahamas", code="BS", continent=continents["SA"]).save()
        Country(name="Belize", code="BZ", continent=continents["SA"]).save()
        Country(name="Chile", code="CL", continent=continents["SA"]).save()
        Country(name="Colombia", code="CO", continent=continents["SA"]).save()
        Country(name="Costa Rica", code="CR", continent=continents["SA"]).save()
        Country(name="Cuba", code="CU", continent=continents["SA"]).save()
        Country(name="Dominica", code="DM", continent=continents["SA"]).save()
        Country(name="Dominican Republic", code="DO", continent=continents["SA"]).save()
        Country(name="Ecuador", code="EC", continent=continents["SA"]).save()
        Country(name="Falkland Islands (Malvinas)", code="FK", continent=continents["SA"]).save()
        Country(name="Grenada", code="GD", continent=continents["SA"]).save()
        Country(name="French Guiana", code="GF", continent=continents["SA"]).save()
        Country(name="Greenland", code="GL", continent=continents["SA"]).save()
        Country(name="Guadeloupe", code="GP", continent=continents["SA"]).save()
        Country(name="South Georgia and the South Sandwich Islands", code="GS", continent=continents["SA"]).save()
        Country(name="Guatemala", code="GT", continent=continents["SA"]).save()
        Country(name="Guyana", code="GY", continent=continents["SA"]).save()
        Country(name="Honduras", code="HN", continent=continents["SA"]).save()
        Country(name="Haiti", code="HT", continent=continents["SA"]).save()
        Country(name="Jamaica", code="JM", continent=continents["SA"]).save()
        Country(name="Saint Kitts and Nevis", code="KN", continent=continents["SA"]).save()
        Country(name="Cayman Islands", code="KY", continent=continents["SA"]).save()
        Country(name="Saint Lucia", code="LC", continent=continents["SA"]).save()
        Country(name="Martinique", code="MQ", continent=continents["SA"]).save()
        Country(name="Montserrat", code="MS", continent=continents["SA"]).save()
        Country(name="Nicaragua", code="NI", continent=continents["SA"]).save()
        Country(name="Panama", code="PA", continent=continents["SA"]).save()
        Country(name="Peru", code="PE", continent=continents["SA"]).save()
        Country(name="Saint Pierre and Miquelon", code="PM", continent=continents["SA"]).save()
        Country(name="Puerto Rico", code="PR", continent=continents["SA"]).save()
        Country(name="Paraguay", code="PY", continent=continents["SA"]).save()
        Country(name="Suriname", code="SR", continent=continents["SA"]).save()
        Country(name="El Salvador", code="SV", continent=continents["SA"]).save()
        Country(name="Turks and Caicos Islands", code="TC", continent=continents["SA"]).save()
        Country(name="Trinidad and Tobago", code="TT", continent=continents["SA"]).save()
        Country(name="Uruguay", code="UY", continent=continents["SA"]).save()
        Country(name="Saint Vincent and the Grenadines", code="VC", continent=continents["SA"]).save()
        Country(name="Venezuela", code="VE", continent=continents["SA"]).save()
        Country(name="Virgin Islands, British", code="VG", continent=continents["SA"]).save()
        Country(name="Virgin Islands, U.S.", code="VI", continent=continents["SA"]).save()

        return HttpResponse("ok.")
