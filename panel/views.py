from django.shortcuts import render
from django.http import JsonResponse,HttpResponse,HttpResponseBadRequest
from django.shortcuts import render,get_object_or_404,redirect
from asgiref.sync import sync_to_async
from installation.models import SiteModel
import time,asyncio
from django.core.paginator import Paginator
from .decorators import unauthenticated_user,allowed_users
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import View
from .forms import *
from.utils import get_current_writers
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
import json
from django.views.decorators.cache import cache_page
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.conf import settings
from rest_framework.decorators import api_view
import re
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.hashers import make_password
from django.db.models import Avg
import timeago,datetime
from  django.contrib.auth.models import Group


CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

def check_data():
  if SiteModel.objects.count() > 0:
    obj=SiteModel.objects.all()[0]
    return obj

#Home
class Home(View):
    def get(self,request):
        if not check_data():
            return redirect('/installation/')
        obj=check_data()
        meters=MeterModel.objects.all().order_by("-id")
        form=ReadingForm()
        form1=HomeForm()
        data={
            'title':f'Welcome to {obj.site_name}',
            'obj':obj,
            'data':request.user,
            'meters':meters,
            'form':form,
            'form1':form1,
        }
        return render(request,'panel/index.html',context=data)
    def post(self,request,*args ,**kwargs):
        form=ReadingForm(request.POST or None)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.user=request.user
            obj.parent=form.cleaned_data.get('meter_name',None)
            obj.save()
            return JsonResponse({'valid':True,'message':'Meter readings submitted successfuly.'},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors,},content_type='application/json')


class weeklyConsuption(View):
    def get(self,request):
        obj=check_data()
        data=ReadingModel.objects.all().order_by("-id")
        paginator=Paginator(data,30)
        page_num=request.GET.get('page')
        readings=paginator.get_page(page_num)
        data={
            'title':'weekly Consuption',
            'obj':obj,
            'data':request.user,
            'readings':readings,
        }
        return render(request,'panel/consuption.html',context=data)


class costCalculator(View):
    def get(self,request):
        obj=check_data()
        form=CostForm()
        equipments=EquipmentModel.objects.all().order_by("-id")
        data={
            'title':'Cost calculator',
            'obj':obj,
            'data':request.user,
            'form':form,
            'equipments':equipments,
        }
        return render(request,'panel/cost_calculator.html',context=data)
    def post(self,request,*args ,**kwargs):
        form=CostForm(request.POST or None)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.user=request.user
            obj.parent=form.cleaned_data.get('meter_name',None)
            obj.save()
            return JsonResponse({'valid':True,'message':'Equipment readings submitted successfuly.'},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors,},content_type='application/json')

@method_decorator(unauthenticated_user,name='dispatch')
class Login(View):
    def get(self,request):
        obj=check_data()
        form=UserLoginForm()
        data={
            'title':'Login',
            'obj':obj,
            'data':request.user,
            'form':form,
        }
        return render(request,'panel/login.html',context=data)
    def post(self,request):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            key=request.POST['username']
            password=request.POST['password']
            if key:
                if password:
                    regex=re.compile(r'([A-Za-z0-9+[.-_]])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z/a-z]{2,})+')
                    if re.fullmatch(regex,key):
                        #email address
                        if User.objects.filter(email=key).exists():
                            data=User.objects.get(email=key)
                            user=authenticate(username=data.username,password=password)
                        else:
                            uform_errors={"username": ["Invalid email address."]}
                            return JsonResponse({'valid':False,'uform_errors':uform_errors},content_type="application/json")
                    else:
                        #username
                        if User.objects.filter(username=key).exists():
                            data=User.objects.get(username=key)
                            user=authenticate(username=key,password=password)
                        else:
                            uform_errors={"username": ["Invalid username."]}
                            return JsonResponse({'valid':False,'uform_errors':uform_errors},content_type="application/json")
                        
                    if user is not None:
                        if 'rememberme' in request.POST:
                           request.session.set_expiry(1209600) #two weeeks
                        else:
                           request.session.set_expiry(0)
                        login(request,user)
                        return JsonResponse({'valid':True,'message':'success:Login Successfully.','login':True},content_type="application/json")
                    uform_errors={"password": ["Password is incorrect."]}
                    return JsonResponse({'valid':False,'uform_errors':uform_errors},content_type="application/json")
                else:
                    uform_errors={"password": ["Password is required."]}
                    return JsonResponse({'valid':False,'uform_errors':uform_errors},content_type="application/json")
            else:
                uform_errors={"username": ["Username/Email Address is required."]}
                return JsonResponse({'valid':False,'uform_errors':uform_errors},content_type="application/json")


def user_logout(request):
    logout(request)
    return redirect('/accounts/login')

@method_decorator(login_required(login_url='/accounts/login'),name='dispatch')
class Dashboard(View):
    def get(self,request):
        obj=check_data()
        form1=SiteForm(instance=obj)
        form2=AddressConfigForm(instance=obj)
        form3=SiteSocialForm(instance=obj)
        form4=WorkingConfigForm(instance=obj)
        form5=MeterForm()
        form6=EquipmentForm()
        obj=check_data()
        data={
            'title':'Dashboard',
            'obj':obj,
            'data':request.user,
            'form1':form1,
            'form2':form2,
            'form3':form3,
            'form4':form4,
            'form5':form5,
            'form6':form6,
        }
        return render(request,'panel/dashboard.html',context=data)
    def post(self,request,*args , **kwargs):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            instance_data=SiteModel.objects.all().first()
            form=SiteForm(request.POST,request.FILES or None , instance=instance_data)
            if form.is_valid():
                form.save()
                return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
            else:
                return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')


#ProfileView
@method_decorator(login_required(login_url='/accounts/login'),name='dispatch')
class ProfileView(View):
    def get(self,request,username):
        obj=check_data()
        user = get_object_or_404(User,username=username)
        form=CurrentLoggedInUserProfileChangeForm(request.POST or None,instance=user)
        eform=CurrentAdminExtUserProfileChangeForm(instance=user.extendedauthuser)
        passform=UserPasswordChangeForm()
        profileform=ProfilePicForm()
        form1=UserSocialForm(instance=user.extendedauthuser)
        data={
            'title':f'Edit profile / {user.get_full_name()}',
            'obj':obj,
            'data':request.user,
            'form':form,
            'eform':eform,
            'editor':user,
            'form1':form1,
            'passform':passform,
            'profileform':profileform,
            'room_name':request.user.username,
        }
        return render(request,'panel/profile.html',context=data)
 
    def post(self,request,username,*args ,**kwargs):
        form=CurrentLoggedInUserProfileChangeForm(request.POST or None,instance=request.user)
        if request.user.is_superuser:
            eform=CurrentAdminExtUserProfileChangeForm(request.POST,request.FILES or None, instance=request.user.extendedauthuser)
        elif request.user.extendedauthuser.category == 'customer':
            eform=CurrentCustomerExtUserProfileChangeForm(request.POST,request.FILES or None,instance=request.user.extendedauthuser)
        else:
            eform=CurrentWriterExtUserProfileChangeForm(request.POST,request.FILES or None,instance=request.user.extendedauthuser)
        styles=json.dumps(request.POST.getlist('citation_style'))
        language=json.dumps(request.POST.getlist('native_language'))
        degree=json.dumps(request.POST.getlist('academic_degree'))
        if form.is_valid() and eform.is_valid():
            form.save()
            save_obj=eform.save(commit=False)
            save_obj.citation_style=styles
            save_obj.native_language=language
            save_obj.academic_degree=degree
            save_obj.save()
            activity=ActivityModel.objects.create(icon='<i class="fa fa-user"></i>',title='Profile update',user_id=request.user.pk,name='Made some changes to your profile') 
            activity.save()
            return JsonResponse({'valid':True,'message':'Profile updated successfully.','profile_pic':True},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors,'eform_errors':eform.errors,},content_type='application/json')


#profilePic
@login_required(login_url='/accounts/login')
@api_view(['POST',])
def profilePic(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        profilePicform=ProfilePicForm(request.POST , request.FILES or None , instance=request.user.extendedauthuser)
        if profilePicform.has_changed():
            if profilePicform.is_valid():
                userme=profilePicform.save(commit=False)
                userme.user=request.user
                userme.save()
                activity=ActivityModel.objects.create(icon='<i class="fa fa-picture"></i>',title='Profile picture', user_id=request.user.pk,name='Changed profile picture') 
                activity.save()
                return JsonResponse({'valid':True,'message':'Profile picture updated.'},status=200,safe=False)
            else:
                return JsonResponse({'valid':False,'uform_errors':profilePicform.errors},status=200)    
        return JsonResponse({'valid':False,'error':'No changes made'},content_type='application/json')

#social
@login_required(login_url='/accounts/login')
@api_view(['POST',])
def edit_social_link(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form=UserSocialForm(request.POST or None , instance=request.user.extendedauthuser)
        if form.has_changed():
            if form.is_valid():
                link=form.save(commit=False)
                link.facebook=request.POST['facebook']
                link.twitter=request.POST['twitter']
                link.instagram=request.POST['instagram']
                link.linkedin=request.POST['linkedin']
                link.save()
                activity=ActivityModel.objects.create(icon='<i class="fa fa-link"></i>',title='Social link',user_id=request.user.pk,name='Edited social links') 
                activity.save()
                return JsonResponse({'valid':True,'message':'Social link(s) updated.'},status=200,safe=False)
            else:
                return JsonResponse({'valid':False,'uform_errors':form.errors},status=200)    
        return JsonResponse({'valid':False,'error':'No changes made'},content_type='application/json')

#passwordChange
@login_required(login_url='/accounts/login')
@api_view(['POST',])
def passwordChange(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        passform=UserPasswordChangeForm(request.POST or None,instance=request.user)
        if passform.is_valid():
            user=User.objects.get(username__exact=request.user.username)
            user.password=make_password(passform.cleaned_data.get('password1'))
            user.save()
            activity=ActivityModel.objects.create(icon='<i class="fa fa-lock"></i>',title='Password changed',user_id=request.user.pk,name='Changed password') 
            activity.save()
            update_session_auth_hash(request,request.user)
            return JsonResponse({'valid':True,'message':'Password changed successfully.'},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':passform.errors},content_type='application/json')

#siteContact
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['POST',])
def siteContact(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        instance_data=SiteModel.objects.all().first()
        form=AddressConfigForm(request.POST or None , instance=instance_data)
        if form.is_valid():
            form.save()
            return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')

#siteSocial
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['POST',])
def siteSocial(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        instance_data=SiteModel.objects.all().first()
        form=SiteSocialForm(request.POST or None , instance=instance_data)
        if form.is_valid():
            link=form.save(commit=False)
            link.facebook=request.POST['facebook']
            link.twitter=request.POST['twitter']
            link.instagram=request.POST['instagram']
            link.linkedin=request.POST['linkedin']
            link.whatsapp=request.POST['whatsapp']
            link.youtube=request.POST['youtube']
            link.save()
            return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')

#addMeter
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['POST',])
def addMeter(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form=MeterForm(request.POST or None)
        if form.is_valid():
            usr=form.save(commit=False)
            usr.user=request.user
            usr.save()
            return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')

#addEquipment
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['POST',])
def addEquipment(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form=EquipmentForm(request.POST or None)
        if form.is_valid():
            usr=form.save(commit=False)
            usr.user=request.user
            usr.save()
            return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')

#meters
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['GET',])
def meters(request):
    obj=check_data()
    count=MeterModel.objects.count()
    data=MeterModel.objects.all().order_by("-id")
    paginator=Paginator(data,30)
    page_num=request.GET.get('page')
    meters=paginator.get_page(page_num)
    data={
        'title':'Showing all meters in ICDC',
        'obj':obj,
        'data':request.user,
        'count':count,
        'meters':meters,
    }
    return render(request,'panel/meters.html',context=data)

#equipments
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['GET',])
def equipments(request):
    obj=check_data()
    count=MeterModel.objects.count()
    data=EquipmentModel.objects.all().order_by("-id")
    paginator=Paginator(data,30)
    page_num=request.GET.get('page')
    equipments=paginator.get_page(page_num)
    data={
        'title':'Showing all equipments in ICDC',
        'obj':obj,
        'data':request.user,
        'count':count,
        'equipments':equipments,
    }
    return render(request,'panel/equipments.html',context=data)

#EditMeter
@method_decorator(login_required(login_url='/accounts/login'),name='dispatch')
@method_decorator(allowed_users(allowed_roles=['admins']),name='dispatch')
class EditMeter(View):
    def get(self ,request,id):
        obj=check_data()
        item = get_object_or_404(MeterModel,id=id)
        form=MeterForm(instance=item)    
        data={
            'title':f'Edit meter / {item.name}',
            'obj':obj,
            'data':request.user,
            'form':form,
            'edit':True,
        }
        return render(request,'panel/edit_meter.html',context=data)

    def post(self,request,id,*args ,**kwargs):
        item=get_object_or_404(MeterModel,id=id)
        form=MeterForm(request.POST or None,instance=item)
        if form.is_valid():
            form.save()
            return JsonResponse({'valid':True,'message':'Meter name updated successfuly.'},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors,},content_type='application/json')

#deleteMeter
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['GET',])
def deleteMeter(request,id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            obj=MeterModel.objects.get(id__exact=id)
            obj.delete() 
            return JsonResponse({'valid':True,'message':'Meter name deleted successfully.','id':id},content_type='application/json')       
        except ServiceModel.DoesNotExist:
            return JsonResponse({'valid':False,'message':'Item does not exist'},content_type='application/json')


#EditEquipment
@method_decorator(login_required(login_url='/accounts/login'),name='dispatch')
@method_decorator(allowed_users(allowed_roles=['admins']),name='dispatch')
class EditEquipment(View):
    def get(self ,request,id):
        obj=check_data()
        item = get_object_or_404(EquipmentModel,id=id)
        form=EquipmentForm(instance=item)    
        data={
            'title':f'Edit equipment / {item.name}',
            'obj':obj,
            'data':request.user,
            'form':form,
            'edit':True,
        }
        return render(request,'panel/edit_equipment.html',context=data)

    def post(self,request,id,*args ,**kwargs):
        item=get_object_or_404(EquipmentModel,id=id)
        form=EquipmentForm(request.POST or None,instance=item)
        if form.is_valid():
            form.save()
            return JsonResponse({'valid':True,'message':'Equipment name updated successfuly.'},content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors,},content_type='application/json')


#deleteEquipment
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['GET',])
def deleteEquipment(request,id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            obj=EquipmentModel.objects.get(id__exact=id)
            obj.delete() 
            return JsonResponse({'valid':True,'message':'Equipment name deleted successfully.','id':id},content_type='application/json')       
        except ServiceModel.DoesNotExist:
            return JsonResponse({'valid':False,'message':'Item does not exist'},content_type='application/json')

#homeUpdater
@login_required(login_url='/accounts/login')
@allowed_users(allowed_roles=['admins'])
@api_view(['POST',])
def homeUpdater(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form=HomeForm(request.POST or None)
        if form.is_valid():
            usr=form.save(commit=False)
            usr.user=request.user
            usr.save()
            return JsonResponse({'valid':True,'message':'data saved successfully'},status=200,content_type='application/json')
        else:
            return JsonResponse({'valid':False,'uform_errors':form.errors},status=200,content_type='application/json')