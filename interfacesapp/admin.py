from django.contrib import admin
from .models  import Vpn, Interface, Rutas


# Register your models here.
admin.site.register(Vpn)
admin.site.register(Interface)
admin.site.register(Rutas)