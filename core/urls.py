from django.contrib import admin
from django.urls import path
from .views import Home, UserUpdateView, GeneralPage, chrome_download, firefox_download, userstastics, Delete_user, Usercreation, chrome_bot_download, firefox_bot_download, single_userstastics

app_name = "core"

urlpatterns = [
    path('home/', Home.as_view(), name="home" ),
    path('userdetail/<slug:userid>/', userstastics.as_view(), name="userdetail" ),
    path('userdetails/', single_userstastics.as_view(), name="single_userstastics" ),
    path('deleteuser/<slug:userid>/', Delete_user.as_view(), name="delete_user" ),
    path('update/<slug:userid>/', UserUpdateView.as_view(), name="update" ),
    path('create-user', Usercreation.as_view(), name="create_user" ),
    path('', GeneralPage.as_view(), name="index" ),
    path('chrome-download', chrome_download, name="chrome-download"),
    path('firefox-download', firefox_download, name="firefox-download"),
    path('chrome-bot-download', chrome_bot_download, name="chrome-bot-download"),
    path('firefox-bot-download', firefox_bot_download, name="firefox-bot-download"),
]
