from django.urls import path
from django import views
from . import views
from .views import *
from django.contrib.auth import views as auth_views


urlpatterns=[
    path('',Home.as_view(),name='home'),
    path('weekly/consuption',weeklyConsuption.as_view(),name='weekly consuption'),
    path('cost/calculator',costCalculator.as_view(),name='cost calculator'),
    path('accounts/login',Login.as_view(),name='login'),
    path('dashboard',Dashboard.as_view(),name='dashboard'),
    path('accounts/logout',views.user_logout,name='logout'),
    path('accounts/reset/password',auth_views.PasswordResetView.as_view(form_class=UserResetPassword,extra_context={'title':'Password Reset'},template_name='panel/password_reset.html'),{'title':'Password Reset'},name='password_reset'),
    path('accounts/reset/password/done',auth_views.PasswordResetDoneView.as_view(template_name='panel/password_reset_done.html'),name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>',auth_views.PasswordResetConfirmView.as_view(template_name='panel/password_reset_confirm.html'),name='password_reset_confirm'),
    path('reset/password/success',auth_views.PasswordResetCompleteView.as_view(template_name='panel/password_reset_complete.html'),name='password_reset_complete'),
    path('<str:username>',ProfileView.as_view(),name='profile'),
    path('change/profile/pic',views.profilePic,name='profile pic'),
    path('edit/social/links',views.edit_social_link,name='edit social link'),
    path('password/change',views.passwordChange,name='password change'),
    path('site/contact',views.siteContact,name='site contact'),
    path('site/social/links/settings',views.siteSocial,name='site social links'),
    path('add/meter/',views.addMeter,name='add meter'),
    path('edit/meter/<int:id>',EditMeter.as_view(),name='edit meter'),
    path('delete/meter/<int:id>',views.deleteMeter,name='delete meter'),
    path('add/equipment/',views.addEquipment,name='add equipment'),
    path('meters/',views.meters,name='meters'),
    path('equipments/',views.equipments,name='equipments'),
    path('edit/equipment/<int:id>',EditEquipment.as_view(),name='edit equipment'),
    path('delete/equipment/<int:id>',views.deleteEquipment,name='delete equipment'),
    #home updater
    path('home/updater',views.homeUpdater,name='home updater'),
]
