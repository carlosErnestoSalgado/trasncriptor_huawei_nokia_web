
import ipaddress
import json
import re 
import math
import io, zipfile


def generate_zipFile(outputs, vlan):
    if isinstance(outputs, list):
        # Crear un archivo ZIP para múltiples salidas
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, output in enumerate(outputs):
                zip_file.writestr(f"servicio_vpn_nokia_{vlan}_{i+1}.txt", output)
        
        zip_buffer.seek(0)
        return zip_buffer
    elif isinstance(outputs, str):
        return outputs
def limpiar_interfaces(all_interfaces):  
    all_interfaces_clean = []  
    for interfaz in all_interfaces:  
        if interfaz['svlan']  and interfaz['ip_address']:  
            all_interfaces_clean.append(interfaz)  
    return all_interfaces_clean

def convertir_interfaces_a_diccionarios(nombre_archivo):  
    interfaces = []  

    try:  
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:  
            lines = archivo.readlines()  
            current_interface = {}  

            for line in lines:  
                line = line.strip()  
                
                if line.startswith("interface"):  
                    # Si ya había una interfaz en progreso, guardamos el diccionario  
                    if current_interface:  
                        # Verificar si la interfaz ya existe en la lista
                        if not any(interface["name"] == current_interface["name"] for interface in interfaces):
                            interfaces.append(current_interface)  
                    
                    # Iniciar un nuevo diccionario para la nueva interfaz  
                    current_interface = {  
                        "name": line.split()[1],  # Obtener el nombre de la interfaz  
                        "description": "",
                        "svlan": "",
                        "cvlan": "",
                        "vpn-instance": "",
                        "qos-profile": "",  
                        "ip_address": "",  
                        "traffic-policy": "",
                        "subnet_mask": "", "static_routes" : []
                    }  
                
                elif line.startswith("description"):  
                    current_interface["description"] = line.split("description", 1)[1].strip().replace('"','')  
                
                elif line.startswith("qinq termination pe-vid"):
                    parts = line.split()
                    current_interface["svlan"] = parts[3]
                    current_interface["cvlan"] = parts[5]
                    
                    # current_interface['svlan'] = line.split("qinq termination pe-vid", 1)[1].strip()
                elif line.startswith("control-vid"): 
                    parts = line.split()
                    current_interface["svlan"] = parts[1]
                    current_interface["cvlan"] = 0
                    
                elif line.startswith("qos-profile"):
                    parts = line.split()
                    if len(parts) >= 2:
                        current_interface["qos-profile"] = parts[1]
                
                elif line.startswith("ip binding vpn-instance"):
                    current_interface["vpn-instance"] = line.split("ip binding vpn-instance", 1)[1].strip()
                
                elif line.startswith("ip address"):  
                    parts = line.split()  
                    if len(parts) >= 3:  
                        current_interface["ip_address"] = parts[2]
                        prefix = mask_to_prefix(parts[3])
                        current_interface["subnet_mask"] = prefix 

                elif line.startswith("traffic-policy"):
                    parts = line.split()
                    if len(parts) >= 3:
                        current_interface['traffic-policy'] = parts[1]
                        
                    
            # Añadir la última interfaz procesada  
            if current_interface:  
                interfaces.append(current_interface)  
        
        return interfaces  

    except FileNotFoundError:  
        print("El archivo no fue encontrado.")  
        return None  
    except Exception as e:  
        print(f"Ocurrió un error: {e}")  
        return None  

def mask_to_prefix(mask):  
    try:  
        # Crear un objeto de red a partir de la máscara  
        net = ipaddress.ip_network(f'0.0.0.0/{mask}', strict=False)  
        # Retornar la longitud del prefijo  
        return net.prefixlen  
    except ValueError:  
        return "Máscara no válida"  

def limpiar_interfaces(all_interfaces):  
    all_interfaces_clean = []  
    for interfaz in all_interfaces:  
        if interfaz['svlan']  and interfaz['ip_address']:  
            all_interfaces_clean.append(interfaz)  
    return all_interfaces_clean

def generate_json(interfaces, pathRD, pathRS, pathSV, generateJson):
    ## Conformacion del Json
    # Obtengo datos necesarios
    all_interfaces = interfaces
    

    vpns = get_rd(pathRD) # VPN's
    
    statics_routes = get_statics_routes(pathRS)

    
    statics_routes_internet = get_routes_internet(pathRS) # Internet

    
    
    # print("RUTAS ESTATICAS: ", len(statics_routes_internet))
    # Ordeno las vpns con sus respectivas interfaces  
    for vpn in vpns:
        for interfaz in all_interfaces:
            # LOGICA PARA NO FILTRART LAS INTERFACES DE DESBORDE DE LOS DSLAM
            filtrar = True
            name =  interfaz['name'].split('.')
            if name[0] == 'GigabitEthernet2/0/11' or name == 'GigabitEthernet3/0/9':
                filtrar = False
            # LOGICA PARA NO FILTRART LAS INTERFACES DE DESBORDE DE LOS DSLAM
            if vpn['vpn-instance'] == interfaz['vpn-instance']:
                lista_comprobacion = ['ED01', ' PR ', ' PR' , 'P del Rio', 'Pinar del Rio', 'Pinar', 'P.DEL.RIO', 'FD01', ' PRI ']
                for palabra in lista_comprobacion:
                    if not filtrar:
                        vpn['interfaces'].append(interfaz)
                    else:
                        if palabra in interfaz['description']:
                            vpn['interfaces'].append(interfaz) 
    for entry in vpns:  
                vpn_instance = entry['vpn-instance']  
            
                for interfaz in entry['interfaces']:  
                    ip_address = interfaz['ip_address']  
                    subnet_mask = interfaz['subnet_mask']  
                    static_routes = []  

                # Buscar rutas que coincidan con la vpn-instance  
                    for route  in statics_routes:  
                        if route['vpn-instance'] == vpn_instance:  
                            # Comprobar si la WAN de la ruta está en el rango de la IP de la interfaz  
                            if ip_in_range(route['wan'], ip_address, subnet_mask):
                                static_routes.append(route)  
                                
                    # Asignar las rutas estáticas encontradas 
                    for route in static_routes:
                        route['description'] = interfaz.get('description', '')  # Use .get() to avoid KeyError
                    interfaz['static_routes'] = static_routes
    
    if generateJson:
        # # Crear un archivo de texto para indicar que ha terminado  
        with open("conversion_result.json", "w") as f:  
            json.dump(vpns, f, indent=4)
        
    #  GENERANDO JSON PARA ALMACENAR SERVICIOS DE INTERNET  #
    internet_services = []
    for interfaz in all_interfaces:
        if interfaz['traffic-policy'] == 'Internet':
            internet_services.append(interfaz)
            for route in statics_routes_internet:
                if are_ips_in_same_subnet(interfaz['ip_address'], route['wan'], interfaz['subnet_mask']):
                    interfaz['static_routes'].append(route)
    if generateJson:
        with open("conversion_result_internet.json", "w") as f: 
            json.dump(internet_services, f, indent=4)
                
    return [vpns, internet_services]
def get_rd(pathRD):
    vpn_istances = []
    
    # RUTA A STATICS ROUTES D:\____ETECSA_____\Transmisión\Alta disponibilidad\programa_python\interfaces\VPN_ME60_CUB.txt
    with open(f'{pathRD}', 'r') as f:
        lines = f.readlines()
        current_vpn_instance = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('ip vpn-instance'):
                parts = line.split()
                
                if len(parts) > 3:
                    rd = parts[4].split(':')
                    id_nokia = rd[0] + rd[1]
                    current_vpn_instance = {
                        'vpn-instance': parts[2],
                        'rd': rd,
                        'interfaces': [],
                        'id_nokia': id_nokia
                    }
                    vpn_istances.append(current_vpn_instance)
            
    return vpn_istances
def get_statics_routes(pathRS):  
    routes_vpn = []  
    try:  
        print("OBTENIENDO RUTAS ESTATICAS")
        # D:/____ETECSA_____/Transmisión/Alta disponibilidad/programa_python/interfaces/ME60CUB.txt
        with open(f'{pathRS}', 'r') as f:  
            lines = f.readlines()  
            print(f"Número de líneas: {len(lines)}, Tipo de líneas: {type(lines)}")  
        
            for line in lines:  
                line = line.strip()  
                
                # Solo procesamos líneas que empiezan con 'ip route-static'  
                if line.startswith('ip route-static vpn-instance'):  
                    parts = line.split()  
                    
                    # Aseguramos que tenga suficientes partes para evitar IndexError  
                    if len(parts) >= 6:
                        current_route = {  
                            'vpn-instance': parts[3],  
                            'lan': parts[4],  
                            'lan_mask': parts[5],  
                            'wan': parts[6],
                            'description': ' '.join(parts[8:]) if len(parts) > 7 else ''  # Manejo del campo de descripción  
                        }  
                        # Añadimos la ruta solo si está completa  
                        routes_vpn.append(current_route)
                        
        return routes_vpn            


    except FileNotFoundError:  
        print(f"El archivo no existe")  
        return None  
    except Exception as e:  
        print(f"Error: {e}")  
        return None  
def get_routes_internet(pathRD):
    routes_internet = []
    #interfaces/ME60CUB.txt
    with open(f'{pathRD}', 'r') as json_file:
        lines = json_file.readlines()
        for line in lines:
            line = line.strip() 
            if line.startswith('ip route-static'):
                parts = line.split()
                if len(parts) >= 5:
                    if not parts.__contains__('vpn-instance'):
                        current_route = { 
                            'lan': parts[2],
                            'lan_mask': parts[3],
                            'wan': parts[4],
                            'description': ' '.join(parts[6:] if len(parts) > 5 else '')                
                        }  
                        # print(current_route)
                        routes_internet.append(current_route)
        # with open('statics-routes-internet.json', 'w') as json_file:
        #         json.dump(routes_internet, json_file, indent=4)

    return routes_internet
def get_routes_internet_ne40(pathRD):
    routes_internet = []
    #interfaces/ME60CUB.txt
    with open(f'{pathRD}', 'r') as json_file:
        lines = json_file.readlines()
        for line in lines:
            line = line.strip() 
            if line.startswith('ip route-static'):
                parts = line.split()
                if not 'vpn-instance' in parts:
                    current_route = { 
                        'lan': parts[2],
                        'lan_mask': parts[3],
                        'wan': parts[4],
                        'description': ' '.join(parts[6:] if len(parts) > 5 else '')                
                    }  
                        
                routes_internet.append(current_route)
        # with open('statics-routes-internet.json', 'w') as json_file:
        #         json.dump(routes_internet, json_file, indent=4)

    return routes_internet

def extraer_interfaces_dslam_ne40(pathInterface, svlan):
    
    with open(pathInterface, 'r', encoding='utf-8') as archivo:
        lines = archivo.readlines()
        interfaces = []
        current_interface = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('interface'):
                print("############################################################")
                parts = line.split()
                # Si ya se creo una interfaz la agrego
                if current_interface:
                    interfaces.append(current_interface)
                
                # Iniciar un nuevo diccionario para la nueva interfaz  
                current_interface = {  
                    "name": parts[1], 
                    "description": "",
                    "svlan": svlan,
                    "cvlan": "",
                    "vpn-instance": "", 
                    "ip_address": "", 
                    "qos-profile": "", 
                    "traffic-policy": "",
                    "subnet_mask": "", "static_routes" : []
                }  
            elif line.startswith('vlan-type'):
                vlan_cliente = line.split()[3]
                print("VLAN CLIENTE: ", vlan_cliente)
                current_interface['cvlan'] = vlan_cliente
                
            elif line.startswith('description'):
                description = line.split('description', 1)[1].strip()
                print("DESCRIPTION: ", description)
                current_interface['description'] = description
            elif line.startswith('ip binding vpn-instance'):
                vpn_instance = line.split('ip binding vpn-instance', 1)[1].strip()
                print("VPN:", vpn_instance)
                current_interface['vpn-instance'] = vpn_instance
            elif line.startswith('ip address'):
                network = line.split()
                ip      = network[2]
                mask    = network[3]
                print("DIRECCION: ", ip, mask)
                current_interface["ip_address"] = ip
                current_interface["subnet_mask"] = mask
            elif line.startswith('traffic-policy'):
                line = line.split()
                trafic_policy = line[1]
                print("TRAFFIC-POLICY: ", trafic_policy )
                current_interface["traffic-policy"] = trafic_policy
        # Añadir la última interfaz procesada  
        if current_interface:  
            interfaces.append(current_interface)  
        
    with open('dslam_ne40.json', '+w') as json_file:
        json.dump(interfaces, json_file, indent=4)
    return interfaces



## FUNCIONES COMPLEMENTARIAS PARA GENERAR LA SALIDA EN FORMATO NOKIA
def generar_interface(description, wan, mask, qos, cvlan, is_dslam_conecct, is_stacking, svlan, backup):  
    interface_name = generate_interface_name(description)  
    
    mask = mask_to_prefix(mask)
    # Base de la configuración de la interfaz  
    config = f'''  
    interface "{interface_name}" create  
        no shutdown  
        description "{interface_name}"  
        address {wan}/{mask}  
        ip-mtu 1618
        sap pw-{2 if backup else 1}{svlan if not is_stacking else cvlan}:{svlan if not is_stacking else cvlan}{'.' + cvlan if is_dslam_conecct else ''} create'''       
    # # Agregar qos solo si tiene valor significativo  
    if qos:  
        config += f'{generar_qos(qos)}'  
        config += '        exit \n    exit'  
    else:
        config += '\n        exit'
        config += '\n    exit'
    return config 
def generate_interface_name(description):
    if type(description) == str:
        description = description.split()
        description.insert(0, 'PR')
        interface_name = ('-'.join(description[:2]).upper() + '_' + '_'.join(description[2:]).upper()).replace('"','')
        interface_name = interface_name.rstrip('_')
        # # Truncar el nombre si excede el número máximo de caracteres
        # if len(interface_name) > 32:
        #     interface_name = interface_name[:32]
        return interface_name
def generar_qos(rate):
    qos = buscar_numeros_y_unidades(rate)
    speed = int(qos[0][0])
    unidad = qos[0][1]
    multiplo =  multiplo = 1000 if unidad == 'Mb' else 1 
    return f'''
            ingress
                qos 10
                queue-override
                    queue 1 create
                        rate {speed * multiplo * 2}
                    exit
                exit
            exit
            egress
                qos 10
                queue-override
                    queue 1 create
                        rate {speed * multiplo * 2}
                    exit
                exit
            exit
'''
    # Expresión regular que busca números de 1 a 3 cifras seguidos de KB o MB      
def generar_vpn(vpn_instance, rd):
    descriptin_list = ['vprn', vpn_instance]
    vprn = '_'.join(descriptin_list).upper()
    rd = rd.split(":")
    rd = [int(item) for item in rd]
    return f'''
-----------------------------------------------------------------------------------
echo "WARNING: Tener presente si la VPRN esta creada"
-----------------------------------------------------------------------------------
CONSULTE: configure service vprn {str(rd[0]) + str(rd[1])}
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
def generar_service_tunnels(ip, svlan, cvlan, is_stacking, backup):
    ip = formatear_numero(ip)
    return f'''
configure service sdp {2 if backup else 1}{ip}1 
    binding
        pw-port {2 if backup else 1}{svlan if not is_stacking else cvlan} vc-id 48{svlan if not is_stacking else cvlan}007 create
            monitor-oper-group "conexion-BB"
            no shutdown
        exit
    exit
'''
def generate_statics_routes(route):
    static_route =  f'''
    static-route-entry {route.lan}/{mask_to_prefix(route.lan_mask)}
        next-hop {route.wan}
            no shutdown
            description "{generate_interface_name(route.description)}"
        exit
    exit'''
    return static_route
def generar_pw(description, svlan, cvlan, is_dslam_connect, is_stacking, backup):
    if is_dslam_connect:
        config = f'''
    configure pw-port {2 if backup else 1}{svlan} create
        description "{generate_interface_name(description)}"
        encap-type qinq
        exit
    exit  
    '''
        return config
    else:
        config = f'''
configure pw-port {2 if backup else 1}{svlan if not is_stacking else cvlan} create
    description "{generate_interface_name(description)}"
exit
'''
        return config

## FUNCIONES DE APOYO
def remove_duplicates(dict_list):  
    seen = set()  
    unique_list = []  

    for d in dict_list:  
        # Helper function para convertir valores no hashables en hashables  
        def to_hashable(val):  
            if isinstance(val, dict):  
                return frozenset((k, to_hashable(v)) for k, v in val.items())  
            elif isinstance(val, list):  
                return tuple(to_hashable(item) for item in val)  
            return val  

        # Convertir el diccionario en un 'frozenset' de sus elementos  
        item_tuple = frozenset((k, to_hashable(v)) for k, v in d.items())  
        
        if item_tuple not in seen:  
            seen.add(item_tuple)  
            unique_list.append(d)  
            
    return unique_list  
def formatear_numero(num):
    # Convertir el número a string  
    num_str = str(num)  
    # Verificar la longitud  
    if len(num_str) == 2:  
        return '0' + num_str  
    elif len(num_str) == 3:  
        return num_str  
    else:  
        return "El número no tiene 2 o 3 dígitos"
def buscar_numeros_y_unidades(s):  
    patron = r'(\d{1,3})(Kb|Mb)'  
    
    # Buscar los números y las unidades en la cadena  
    coincidencias = re.findall(patron, s)  
    
    return coincidencias  
def get_list_of_svlans_dslam(path):
    svlans = []
    
    with open(path, 'r') as f:
        data = f.readlines()
        data_print = []
        for line in data:
            data_print.append(int(line.replace('\n', '')))
    return(data_print)
def ip_in_range(ip_address, lan_address, lan_mask):  
    ip = ipaddress.ip_address(ip_address)  
    network = ipaddress.ip_network(f"{lan_address}/{lan_mask}", strict=False)  
    return ip in network  
def are_ips_in_same_subnet(ip1, ip2, mask):  
    
    try:  
        # Convertimos las direcciones IP a objetos de dirección IP  
        ip_addr1 = ipaddress.ip_address(ip1)  
        ip_addr2 = ipaddress.ip_address(ip2)  

        # Definimos la subred usando la máscara  
        subnet = ipaddress.ip_network(f"{ip1}/{mask}", strict=False)  

        # Verificamos si ambas IPs están en la misma subred  
        return ip_addr1 in subnet and ip_addr2 in subnet  

    except ValueError as e:  
        print(f"Error: {e}")  
        return False  

def organizar_por_vpn(datos):
    
    vpn_dict = {}  # Usamos un diccionario para agrupar por VPN

    for item in datos:
        vpn_instance = item['vpn-instance']
        interface = item['interface']

        # Si la VPN no está en el diccionario, la agregamos
        if vpn_instance not in vpn_dict:
            vpn_dict[vpn_instance] = {
                'vpn-instance': vpn_instance,
                'rd': item['rd'],
                'interfaces': []
            }

        # Agregamos la interfaz a la lista de interfaces de la VPN
        vpn_dict[vpn_instance]['interfaces'].append(interface)

    # Convertimos el diccionario a una lista de diccionarios
    vpn_list = list(vpn_dict.values())

    return vpn_list

def generate_range_ip():
    # Genero rango de ip
    rango_ip = list(range(33, 135))
    rango_ip = [str(item) for item in rango_ip]
    return rango_ip

def ip_anterior(ip_address):  
    ip = ipaddress.ip_address(ip_address)  
    ip_anterior = ip - 1
    return ip_anterior


def get_subnet(mask):
    last_octet = mask.split('.')[-1]
    r1 = 256 - int(last_octet)
    r2 = math.log2(r1)
    r3 = 32 - r2
    return int(r3)   

def get_subnet_beibi(mask):
    mask = mask.split('.')
    mask = [bin(int(item)) for item in mask]
    mask = [str(item).removeprefix('0b') for item in mask]
    # for index, item in enumerate(mask):
    #     if item == '0':
    #         mask[index] = '00000000'
    mask = ''.join(mask)
    bits = mask.count('1')
    return bits

def subnet_mask_from_slash(slash):
    return str(ipaddress.IPv4Network((0, slash)).netmask)
