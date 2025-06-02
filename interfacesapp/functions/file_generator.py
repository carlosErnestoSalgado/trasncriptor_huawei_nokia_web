from ..models import Interface, Rutas, Vpn
from .utils import *

# GENERAR SALIDA PARA UN SERVICIO DE INTERNET
def generar_internet_service(svlan, ip_equipo, is_stacking):
    try:
        interface = Interface.objects.get(cvlan=svlan)
    except Exception as e:
        return f'Datos no enonctrados. Por favor. Revise todos los campos'
    
    output_bauta = ''

    output_pinar = '''                              
----------------------------------------------------------------
echo SERVICIO EN PINAR DEL RIO
----------------------------------------------------------------
echo # PW-PORT                
----------------------------------------------------------------                              
'''
    output_bauta +='''
----------------------------------------------------------------
echo SERVICIO EN BAUTA
----------------------------------------------------------------
echo # PW-PORT                
----------------------------------------------------------------  
'''
    output_pinar += generar_pw(
    description=f'PW-PORT_{svlan}',
    svlan=interface.svlan,
    cvlan=interface.cvlan,
    is_stacking=is_stacking,
    is_dslam_connect=False,
    backup=False
    )
    output_bauta += generar_pw(
    description=f'PW-PORT_{svlan}',
    svlan=interface.svlan,
    cvlan=interface.cvlan,
    is_stacking=is_stacking,
    is_dslam_connect=False,
    backup=True
    )
    output_pinar+='''
----------------------------------------------------------------
echo # SERVICE TUNELS               
----------------------------------------------------------------                              
'''
    output_bauta += '''
----------------------------------------------------------------
echo # SERVICE TUNELS               
---------------------------------------------------------------- 
'''
    output_pinar += (generar_service_tunnels(
        ip_equipo, 
        svlan= interface.svlan,
        cvlan=interface.cvlan,
        is_stacking=is_stacking,
        backup=False
    ))
    output_bauta += generar_service_tunnels(
        ip_equipo, 
        svlan= interface.svlan,
        cvlan=interface.cvlan,
        is_stacking=is_stacking,
        backup=True
    )
    description = interface.description
    output_pinar+='-----------------------------------------------------------------'
    output_pinar += f'\n#echo SERVICIO INTERNET {description}'
    output_pinar +='\n-----------------------------------------------------------------'
    output_pinar += '\n# configure service ies 48'
    output_bauta += '''
----------------------------------------------------------------
echo # SERVICIO INTERNET                
---------------------------------------------------------------- 
# configure service ies 48
'''
    output_pinar += generar_interface(
            is_dslam_conecct= False,
            is_stacking= is_stacking,
            cvlan= interface.cvlan,
            svlan= interface.svlan,
            qos= interface.qos_profile if interface.qos_profile else None,
            description= interface.description,
            wan= interface.ip_address,
            mask= interface.subnet_mask,
            backup=False)
    output_bauta += generar_interface(
        is_dslam_conecct= False,
        is_stacking= is_stacking,
        cvlan= interface.cvlan,
        svlan= interface.svlan,
        qos= interface.qos_profile if interface.qos_profile else None,
        description= interface.description,
        wan= interface.ip_address,
        mask= interface.subnet_mask,
        backup=True
    )
    
    internet_rutas = Rutas.objects.filter(vpn_instance_id__isnull=True)
    for ruta in internet_rutas:
        if are_ips_in_same_subnet(interface.ip_address, ruta.wan, interface.subnet_mask):  
            output_pinar += '\n# configure router'
            output_pinar += generate_statics_routes(ruta)
            output_bauta += generate_statics_routes(ruta)
            output_pinar +='\n-----------------------------------------------------------------\n'
    output_pinar += output_bauta

    return output_pinar
# GENERAR SALIDA PARA UNA VPN EN PARTICULAR
def generate_vpn_service(id_vpn, vlan_instance, ip_equipo, is_stacking):
    try:
        # CONSULTA A LA BASE DE DATOS
        vpn = Vpn.objects.get(id=id_vpn)
        interface = Interface.objects.get(id_vpn_instance_id=vpn, cvlan=int(vlan_instance))
        print('[INFO]  INFORMACION OBTENIDA CORRECTAMENTE DE LA BASE DE DATOS')
    
        
        # OBTENER ULTIMO OCTETO DE LA IP
        ip_equipo = ip_equipo.split('.')[-1]
        

        # # Limpiando todas las interfaces duplicadas
        # interfaces = remove_duplicates(vpns[index_vpn]['interfaces'])
        
        # Condicional de DSLAM
        is_dslam_conecct = 0
        
        # Condicion de Stacking
        is_stacking = is_stacking
        
        
        output_bauta = ''
        output = ''
        
        output +='\n#------------------------------------------------------------'
        output +=f'\n echo "Primero se debe crear el Servivio en Capa 2'
        output +='\n#------------------------------------------------------------' 
        output +='\n#------------------------------------------------------------'
        output +=f'\n echo "PW-PORT"'
        output +='\n#------------------------------------------------------------'
        output_bauta += '''
#------------------------------------------------------------
echo SERVICIO EN BAUTA
#------------------------------------------------------------
echo "Primero se debe crear el Servivio en Capa 2
#------------------------------------------------------------
#------------------------------------------------------------
echo "PW-PORT
#------------------------------------------------------------''' 
        output +=generar_pw(
                is_dslam_connect= is_dslam_conecct,
                is_stacking=is_stacking,
                cvlan=interface.cvlan,
                svlan=interface.svlan,
                description=interface.description,
                backup=False
            )
        output_bauta += generar_pw(
                is_dslam_connect= is_dslam_conecct,
                is_stacking=is_stacking,
                cvlan=interface.cvlan,
                svlan=interface.svlan,
                description=interface.description,
                backup=False
            )
        output +='\n#------------------------------------------------------------'
        output +=f'\n echo "Services tunnels"'
        output +='\n#------------------------------------------------------------'
        output_bauta += '''
#------------------------------------------------------------
echo "Services tunnels
#------------------------------------------------------------''' 
        output +=generar_service_tunnels(
                            ip_equipo, 
                            svlan = interface.svlan, 
                            cvlan = interface.cvlan,
                            is_stacking=is_stacking,
                            backup=False
        )
        output_bauta += generar_service_tunnels(
                            ip_equipo, 
                            svlan = interface.svlan, 
                            cvlan = interface.cvlan,
                            is_stacking=is_stacking,
                            backup=True
        )
        # Escribir contenido en el archivo
        
        output +='\n#------------------------------------------------------------'
        output +=f'\n echo "VPRN {vpn.vpn_instance} Interfaces Configuration"'
        output +='\n#------------------------------------------------------------'      
        output += generar_vpn(vpn.vpn_instance, vpn.route_disting)
        output_bauta += f'''
#------------------------------------------------------------
echo VPRN {vpn.vpn_instance} Interfaces Configuration
#------------------------------------------------------------'''
        output_bauta += generar_vpn(vpn.vpn_instance, vpn.route_disting)
        output +=generar_interface(
                # cvlan= interface.cvlan if is_dslam_conecct else None,
                is_dslam_conecct= is_dslam_conecct,
                is_stacking= is_stacking,
                cvlan= interface.cvlan,
                svlan= interface.svlan,
                qos= interface.qos_profile if interface.qos_profile else None,
                description= interface.description,
                #pw=  interface.svlan if not is_stacking else interface.cvlan,
                #pw=  interface.svlan if not is_dslam_conecct else interface.cvlan,
                wan= interface.ip_address,
                mask= interface.subnet_mask,
                backup=False)
                
        rutas = Rutas.objects.filter(vpn_instance_id=vpn)
        rut_temp = ''
        for ruta in rutas:
            if are_ips_in_same_subnet(interface.ip_address, ruta.wan, interface.subnet_mask):
                output += generate_statics_routes(ruta) 
                rut_temp =generate_statics_routes(ruta)
        
        output_bauta += generar_interface(
            is_dslam_conecct= is_dslam_conecct,
                is_stacking= is_stacking,
                cvlan= interface.cvlan,
                svlan= interface.svlan,
                qos= interface.qos_profile if interface.qos_profile else None,
                description= interface.description,
                #pw=  interface.svlan if not is_stacking else interface.cvlan,
                #pw=  interface.svlan if not is_dslam_conecct else interface.cvlan,
                wan= interface.ip_address,
                mask= interface.subnet_mask,
                backup=True
        )
        output_bauta+=rut_temp
        

        output += '\n---------------------------------------------\n' 
        output += '\n---------------------------------------------\n' 

        return [output, output_bauta]
    except Exception as e:
        return f"[ERROR] {e}"
# GENERAR SALIDA PARA UN DSLAM
def generar_output_dslam(vlan, ip_address):
    VPRN = False  # Futuros checkbox para crear VPRN
    state_name = False # Futuros CheckBox para cortar los nombres de las interfaces a 32 caracteres
    
    try: 
        interfaces = Interface.objects.filter(svlan=vlan)
        print(f'[INFO] DSLAM {vlan} con  ', len(interfaces), ' interfaces')
        print(interfaces.filter(traffic_policy="Internet"))

        output_bauta = '''
#------------------------------------------------------------
BAUTA
#------------------------------------------------------------
echo "DSLAM 1270 Interfaces Configuration"
#------------------------------------------------------------
#------------------------------------------------------------
echo "Primero se debe crear el Servivio en Capa 2
#------------------------------------------------------------
#------------------------------------------------------------
echo "PW-PORT"
#------------------------------------------------------------
'''
        output = '\n#------------------------------------------------------------'
        output += f'\n echo "DSLAM {vlan} Interfaces Configuration"'
        output += '\n#------------------------------------------------------------'
        output += '\n#------------------------------------------------------------'
        output += f'\n echo "Primero se debe crear el Servivio en Capa 2'
        output += '\n#------------------------------------------------------------' 
        output += '\n#------------------------------------------------------------'
        output += f'\n echo "PW-PORT"'
        output += '\n#------------------------------------------------------------'
        
        # Clasificacion de interfaces 
        internet = interfaces.filter(traffic_policy="Internet")
        vpns     = interfaces.filter(traffic_policy="VPN")
        isp_gps  = interfaces.filter(traffic_policy="ISP_GPS")
        nac_smtp = interfaces.filter(traffic_policy="nacional_smtp")

        """
        FALTARIA AGREAGAR DUNCIONABILIDAD PARA LOS SERVICIOS ISP_GPS Y LOS
        SERVICIOS NAC_SMTP
        """
        
        print(f"""
######################################
INTERFACES INTERNET: {len(internet)}
INTERFACES VPN:      {len(vpns)}
INTERFACES SMTP:     {len(isp_gps)}
INTERFACES ISP GPS:  {len(nac_smtp)}
""")
        
        pw_output = generar_pw(
            svlan=vlan,
            cvlan=None,
            is_dslam_connect=True,
            is_stacking=False,
            description=f"PW-DSLAM_{vlan}",
            backup=False
        )
        output += pw_output
        output_bauta += pw_output
        
        output += '\n#------------------------------------------------------------'
        output += f'\n echo "Services tunnels"'
        output += '\n#------------------------------------------------------------' 
        output_bauta += '''
#------------------------------------------------------------
echo "Services tunnels"
#------------------------------------------------------------
'''
        
        service_tunnels_output = generar_service_tunnels(
            ip_address, 
            svlan=vlan, 
            cvlan=None,
            is_stacking=False,
            backup=False
        )
        output += service_tunnels_output
        output_bauta += generar_service_tunnels(
            ip_address, 
            svlan=vlan, 
            cvlan=None,
            is_stacking=False,
            backup=True
        )
        
        output += '\n#------------------------------------------------------------'
        output += f'\n echo "Servicios de Internet"'
        output += '\n#------------------------------------------------------------'
        output_bauta += '''
#------------------------------------------------------------
echo "Servicios de Internet"
#------------------------------------------------------------
'''
        
        for interface in internet:
            description = interface.description
            ip_wan = interface.ip_address
            mask = interface.subnet_mask
            cvlan = interface.cvlan
            
            interface_output = f'''                         
configure services ies 48  
interface "{description}" create  
    shutdown  
    description "{description}"  
    address {ip_wan}/{mask}  
    ip-mtu 1618
    sap pw-1{vlan}:{cvlan} create
    exit
exit
exit'''
            output += interface_output
            output_bauta += interface_output
            
            routes = Rutas.objects.filter(vpn_instance_id__isnull=True)
            for route in routes:
                if are_ips_in_same_subnet(ip1=interface.ip_address, ip2=route.wan, mask=interface.subnet_mask):
                    route_output = '\nconfigure router' + generate_statics_routes(route=route) + '\nexit'
                    output += route_output
                    output_bauta += route_output

        # SERVICIOS DE VPNS
        for interface in vpns:
            vpn = Vpn.objects.get(id=interface.id_vpn_instance.id)
            rd = vpn.route_disting
            descriptin_list = ['vprn', vpn.vpn_instance]
            vprn = '_'.join(descriptin_list).upper()
            rd = rd.split(":")
            rd = [int(item) for item in rd]
            ip_wan = interface.ip_address
            
            if VPRN:
                vprn_output = f'''
-----------------------------------------------------------------------------------
echo "WARNING: Tener presente si la VPRN esta creada"
-----------------------------------------------------------------------------------
CONSULTE: configure service vprn {str(rd[0]) + str(rd[1])} {"BUSCAR RD REAL EN EL NE40 " if rd == '1111:1111' else " "}
-----------------------------------------------------------------------------------
configure service vprn {str(rd[0]) + str(rd[1])} name {vprn} customer 7 create
description "{vprn}"
snmp
    access
exit
route-distinguisher {rd[0]}:{rd[1]}
auto-bind-tunnel
    resolution-filter
        ldp
    exit
    resolution filter
exit
vrf-target target:{rd[0]}:{rd[1]}
no shutdown'''
                output += vprn_output
                output_bauta += vprn_output
            else:
                output += f'\nconfigure service vprn {str(rd[0]) + str(rd[1])}'
                output_bauta += f'\nconfigure service vprn {str(rd[0]) + str(rd[1])}'
                
            interface_name = generate_interface_name(interface.description)
            if len(interface_name) > 32 and state_name:
                print(interface_name, " MAYOR A 32 CARACTERES")
            subnet = get_subnet_beibi(interface.subnet_mask)
            
            vpn_interface_output = f'''
interface "{interface_name}" create  
    shutdown  
    description "{interface_name}"  
    address {interface.ip_address}/{subnet}  
    ip-mtu 1618
    sap pw-1{vlan}:{interface.cvlan} create
    exit
exit'''
            output += vpn_interface_output
            
            vpn_interface_output_bauta = f'''
interface "{interface_name}" create  
    shutdown  
    description "{interface_name}"  
    address {interface.ip_address}/{subnet}  
    ip-mtu 1618
    sap pw-2{vlan}:{interface.cvlan} create
    exit
exit'''
            output_bauta += vpn_interface_output_bauta
            
            routes = Rutas.objects.filter(vpn_instance_id=vpn.id)
            if not routes:
                output += '\nexit'
                output_bauta += '\nexit'
            for route in routes:
                if are_ips_in_same_subnet(interface.ip_address, route.wan, interface.subnet_mask):
                    route_output = generate_statics_routes(route=route) + '\nexit'
                    output += route_output
                    output_bauta += route_output
        
        return [output, output_bauta]
    except Exception as error:
        print("ERROR: ", error)
        return f"Error: {str(error)}"