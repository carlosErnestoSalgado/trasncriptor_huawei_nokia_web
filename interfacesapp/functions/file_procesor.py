from ..models import Vpn,Interface
import ipaddress

def get_rd(pathRD):
    vpn_istances = []
    try:
        with open(f'{pathRD}', 'r') as f:
            lines = f.readlines()
            current_vpn_instance = {}
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('ip vpn-instance'):
                    parts = line.split()
                    
                    if len(parts) > 3:
                        rd = parts[4].split(':')
                        current_vpn_instance = {
                            'vpn_instance': parts[2],
                            'route_disting': parts[4],
                        }
                        vpn_istances.append(current_vpn_instance)
                
        return vpn_istances
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

def get_interfaces(nombre_archivo):  
    interfaces = []  

    try:  
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:  
            lines = archivo.readlines()  
            current_interface = {}  

            for line in lines:  
                line = line.strip()  
                
                if line.startswith("interface"):  
                    # Si ya había una interfaz en progreso, guardamos la instancia  
                    if current_interface:  
                        # Verificar si la interfaz ya existe en la lista
                        if not any(interface.name == current_interface["name"] for interface in interfaces):
                            try:
                                if current_interface['svlan'] and current_interface['ip_address']:
                                    interface = Interface(**current_interface)  
                                    interfaces.append(interface)
                            except Exception as error:
                                print(error)
                                pass  
                    
                    # Iniciar un nuevo diccionario para la nueva interfaz  
                    current_interface = {  
                        "name": line.split()[1],  # Obtener el nombre de la interfaz  
                        "description": "",
                        "svlan": "",
                        "cvlan": "",
                        "qos_profile": "",  
                        "traffic_policy": "",
                        "subnet_mask": "", 
                        "ip_address": "",  
                        "id_vpn_instance": "",
                    }  
                
                elif line.startswith("description"):  
                    current_interface["description"] = line.split("description", 1)[1].strip().replace('"','')  
                
                elif line.startswith("qinq termination pe-vid"):
                    parts = line.split()
                    current_interface["svlan"] = int(parts[3])
                    current_interface["cvlan"] = int(parts[5])
                    
                elif line.startswith("control-vid"): 
                    parts = line.split()
                    current_interface["svlan"] = int(parts[1])
                    current_interface["cvlan"] = 0
                    
                elif line.startswith("qos-profile"):
                    parts = line.split()
                    if len(parts) >= 2:
                        current_interface["qos_profile"] = parts[1]
                
                elif line.startswith("ip binding vpn-instance"):
                    vpn_instance = line.split("ip binding vpn-instance", 1)[1].strip()
                    vpn = Vpn.objects.get(vpn_instance=vpn_instance)
                    current_interface["id_vpn_instance"] = vpn 
                
                elif line.startswith("ip address"):  
                    parts = line.split()  
                    if len(parts) >= 3:  
                        current_interface["ip_address"] = parts[2]
                        current_interface["subnet_mask"] = parts[3]

                elif line.startswith("traffic-policy"):
                    parts = line.split()
                    if len(parts) >= 3:
                        current_interface['traffic_policy'] = parts[1]
                        if parts[1] != 'VPN':
                            current_interface["id_vpn_instance"] = None
                        
            # Añadir la última interfaz procesada  
            if current_interface and current_interface['svlan'] and current_interface['ip_address']:
                try:
                    interface = Interface(**current_interface)  
                    interfaces.append(interface)
                except Exception as error:
                    print(error)
                    pass  
        
        return interfaces
    except FileNotFoundError:  
        print("El archivo no fue encontrado.")  
        return None  
    except Exception as e:  
        print(f"Ocurrió un error: {e}")  
        return None  

def get_statics_routes(pathRS):
    """
    Procesa un archivo de configuración para extraer rutas estáticas, tanto para VPN como globales.
    
    Args:
        pathRS (str): Ruta al archivo de configuración
        
    Returns:
        list: Lista de diccionarios con las rutas encontradas o None en caso de error
    """
    routes = []
    
    try:
        with open(pathRS, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                if not line.startswith('ip route-static'):
                    continue
                    
                try:
                    parts = line.split()
                    route_data = {
                        'vpn_instance': None,
                        'lan': None,
                        'lan_mask': None,
                        'wan': None,
                        'description': None
                    }
                    
                    # Procesamiento para rutas VPN
                    if 'vpn-instance' in parts:
                        vpn_index = parts.index('vpn-instance')
                        vpn_name = parts[vpn_index + 1]
                        
                        try:
                            route_data['vpn_instance'] = Vpn.objects.get(vpn_instance=vpn_name)
                        except Vpn.DoesNotExist:
                            print(f"Advertencia: VPN '{vpn_name}' no encontrada en línea {line_num}")
                            continue
                            
                        # Los campos de red están después del nombre de la VPN
                        network_index = vpn_index + 2
                        if len(parts) > network_index + 2:
                            route_data.update({
                                'lan': parts[network_index],
                                'lan_mask': parts[network_index + 1],
                                'wan': parts[network_index + 2]
                            })
                    
                    # Procesamiento para rutas globales (no VPN)
                    else:
                        if len(parts) >= 5:
                            route_data.update({
                                'lan': parts[2],
                                'lan_mask': parts[3],
                                'wan': parts[4]
                            })
                    
                    # Procesamiento de descripción (opcional)
                    if 'description' in parts:
                        desc_index = parts.index('description')
                        route_data['description'] = ' '.join(parts[desc_index + 1:])
                    
                    # Validar que tenemos los campos mínimos requeridos
                    if route_data['lan'] and route_data['lan_mask'] and route_data['wan']:
                        routes.append(route_data)
                    else:
                        print(f"Advertencia: Ruta incompleta en línea {line_num}")
                        
                except Exception as e:
                    print(f"Error procesando línea {line_num}: {e}")
                    continue
                    
        return routes if routes else None
        
    except FileNotFoundError:
        print(f"Error: Archivo no encontrado - {pathRS}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        return None
    
def mask_to_prefix(mask):  
    try:  
        # Crear un objeto de red a partir de la máscara  
        net = ipaddress.ip_network(f'0.0.0.0/{mask}', strict=False)  
        # Retornar la longitud del prefijo  
        return net.prefixlen  
    except ValueError:  
        return "Máscara no válida"  