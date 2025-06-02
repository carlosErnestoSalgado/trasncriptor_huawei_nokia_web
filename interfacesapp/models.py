from django.db import models


# Create your models here.

class Vpn(models.Model):
    vpn_instance = models.CharField(max_length=100)
    route_disting = models.CharField(max_length=9)

    def __str__(self):
        return self.vpn_instance + '-' + self.route_disting
    
class Interface(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(max_length=300, blank=True)
    svlan = models.PositiveIntegerField(null=True, blank=True)
    cvlan = models.PositiveIntegerField(null=True, blank=True)
    qos_profile = models.CharField( blank=True, null=True)
    traffic_policy = models.CharField( blank=True, null=True)
    subnet_mask = models.CharField( blank=True, null=True)
    ip_address = models.CharField(max_length=15, blank=True, null=True)
    id_vpn_instance = models.ForeignKey(Vpn, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        if self.id_vpn_instance:
            return self.name + " vpn: " + self.id_vpn_instance.vpn_instance
        return self.name + " " + self.traffic_policy
    
# Agregar tabla para rutas estatica
class Rutas(models.Model):
    vpn_instance = models.ForeignKey(Vpn, on_delete=models.CASCADE, null=True, blank=True)
    lan = models.CharField(max_length=15)
    lan_mask = models.CharField(max_length=15)
    wan = models.CharField(max_length=15)
    description = models.CharField(max_length=300, null=True, blank=True) 

    def __str__(self):
        if self.vpn_instance:
            return self.wan + " - " + self.vpn_instance.vpn_instance
        return self.wan