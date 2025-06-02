from django.urls import path
from django.contrib import admin
from . import views


urlpatterns = [
    path("home", views.Index, name="Index"),
    path("create_vpn/", views.CreateVpnView, name="create_vpn"),
    path("create_interface/", views.CreateInterfaceView, name="create_interface"),
    path("cargar_archivos/", views.CargarArchivosView, name='cargar_archivos'),
    path("generate_service/internet", views.GenerarServicioInternetView, name='generate_service'),
    path('generar_service/vpn', views.GenerarServiciosVpnView, name="generate_vpn"),
    path('generate_service/dslam', views.GenerarServiciosDslamView, name="generate_dslam"),
    path('generate_service/smtp', views.GenerarServicioSmtp, name="generate_smtp"),
    path('generate_service/gps', views.GenerarServicioGpsView, name="generate_gps"),
    path('documentation/', views.Documentationview, name="documentation"),
    path('', views.SignupView, name='singup'),
    path('signup/', views.SignupView, name='singup'),
    path('logout/', views.LogoutView , name='logout'),
    path('logout_out/', views.LogoutView , name='logout_out'),
    path('admin/', admin.site.urls, name='admin'),
]
