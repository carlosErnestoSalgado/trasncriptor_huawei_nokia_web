# IMPORTACIONES DE DJANGO
from django.shortcuts import render, HttpResponse, redirect
from django.core.files.storage import FileSystemStorage
from django.contrib import messages

# FROMULARIO DE INICIO DE SESION
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView

# para no usar cache
from django.views.decorators.cache import never_cache

# IMPORTACIONES DE MI PROPIA APP
from .forms import CreateInterface, CreateVpn
from .models import Vpn, Interface, Rutas
from .functions import file_procesor,file_generator, utils

# Importaciones
import io
import zipfile

# Vista principal de Bienvenida
@login_required
def Index(request):
    return render(request, 'Index.html')

# Vistas para llenar Modelos de Formularios
@login_required
def CreateVpnView(request):
    if request.method == "GET":
        data = {
            'form': CreateVpn()
        }
        return render(request, 'forms/createvpn.html', data)
    elif request.method == "POST":
        vpn = Vpn.objects.create(vpn_instance=request.POST['vpn_instance'], route_disting=request.POST['route_disting'])
        return redirect('Index')

@login_required
def CreateInterfaceView(request):
    if request.method == "GET":    
        data = {
            'form': CreateInterface()
        }
        return render(request, 'forms/createinterface.html', data)
    elif request.method == "POST":
        POST = request.POST
        name = POST['name']
        description = POST['description']
        svlan = POST['svlan']
        cvlan = POST['cvlan']
        qos_profile = POST['qos_profile']
        subnet_mask = POST['subnet_mask']
        ip_address = POST['ip_address']
        id_vpn_instance = POST['id_vpn_instance']
        vpn = Vpn.objects.get(id=id_vpn_instance)
        interface = Interface.objects.create(name=name, description=description, svlan=svlan, cvlan=cvlan, qos_profile=qos_profile, subnet_mask=subnet_mask, ip_address=ip_address, id_vpn_instance=vpn)
        return redirect("Index")

@login_required
def CargarArchivosView(request):
    result = None
    print("[REQUEST] "+ str(request.FILES))
    if request.method == "POST":
        # Verificar que ambos tipos de archivos existen
        if not request.FILES.get('file') or not request.FILES.getlist('files_interfaces'):
            messages.error(request, "Debes subir ambos tipos de archivos")
            return render(request, 'forms/cargararchivos.html')
        
        fs = FileSystemStorage()
        temp_files = [] # Para trackear todos los archivos temporales

        try:
            # Procesar archivo VPN unico
            # Guardar el archivo temporalmente
            uploaded_file_vpn = request.FILES['file']
            filename_vpn = fs.save(uploaded_file_vpn.name, uploaded_file_vpn)
            temp_files.append(filename_vpn)
            file_path_vpn = fs.path(filename_vpn)
            
            # Procesar VPNs
            result = file_procesor.get_rd(pathRD=file_path_vpn)
            datos = [Vpn(** item) for item in result] # Copia de todos los objetos
            # Elimino la base de datos para actualizarla por completo 
            # ====> SOLO FASE DE DESARROLLO <==== #
            Vpn.objects.all().delete()
            Vpn.objects.bulk_create(datos)

            # Procesar archivo de interfaces
            uploaded_files_interfaces = request.FILES.getlist('files_interfaces')
            interfaces = [] # Variable para almacenar las interfaces de cada archivo
            for file in uploaded_files_interfaces:
                # Proceso cada archivo de interfaces Subido 
                filename = fs.save(file.name, file)
                temp_files.append(filename)
                file_path = fs.path(filename)
                interfaces.extend(file_procesor.get_interfaces(file_path))
            if interfaces:
                print('INTERFACES ')
                # Elimino la base de datos para actualizarla por completo 
                # ====> SOLO FASE DE DESARROLLO <==== #
                Interface.objects.all().delete()
                Interface.objects.bulk_create(interfaces)
            
            # Procesar las rutas estaticas
            uploaded_files_rutas = request.FILES.getlist('files_rutas')
            print(uploaded_files_rutas)
            rutas = [] # variable para almacenar las rutas de cada archivo
            for ruta in uploaded_files_rutas:
                filename = fs.save(ruta.name, ruta)
                temp_files.append(filename)
                file_path = fs.path(filename)
                rutas.extend(file_procesor.get_statics_routes(file_path))

            print("TOTAL DE RUTAS ", len(rutas))
            
            data = [Rutas(**item) for item in rutas]
            print(len(data))
            Rutas.objects.all().delete()
            Rutas.objects.bulk_create(data)

        except Exception as error:
            messages.error(request, f"ERROR: {error}")
        finally:
            # Elimino el archivo temporal
            for temp_file in temp_files:
                try:
                    fs.delete(temp_file)
                except:
                    pass

    return render(request, 'forms/cargararchivos.html', {'result': result})

@login_required
def GenerarServicioInternetView(request):
    if request.method == "POST":
        print("POST")
        print(request.POST)
        svlan = int(request.POST['vlan'])
        ip = request.POST['ip_address']
        output = file_generator.generar_internet_service(svlan=svlan,ip_equipo=ip, is_stacking=True)
        
        # Crear la respuesta HTTP con el archivo
        response = HttpResponse(output, content_type='text/plain')
        
        # Configurar los headers para forzar la descarga
        response['Content-Disposition'] = f'attachment; filename="servicio_internet_nokia_{svlan}.txt"'

        return response
    
    return render(request, 'forms/generarserviciointernet.html')

@login_required
def GenerarServiciosVpnView(request):
    if request.method == "POST":
        print(request.POST)

        # CAPTURA DE DATOS SOLICITUD POST
        vpn_id = request.POST['vpn_instance']
        vlan         = request.POST['vlan']
        ip           = request.POST['ip_address']

        print(vpn_id, vlan, ip)
        outputs = file_generator.generate_vpn_service(id_vpn=vpn_id, vlan_instance=vlan, ip_equipo=ip, is_stacking=True)

        if isinstance(outputs, list):
            # Crear un archivo ZIP para múltiples salidas
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, output in enumerate(outputs):
                    zip_file.writestr(f"servicio_vpn_nokia_{vlan}_{i+1}.txt", output)
            
            zip_buffer.seek(0)
            response = HttpResponse(zip_buffer, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="servicios_vpn_{vlan}.zip"'
            return response
            
        elif isinstance(outputs, str):
            print(outputs)
            return redirect('Index')
    vpns =[{"id": vpn.id , "vpn_instance":vpn.vpn_instance} for vpn in Vpn.objects.all()]
    
    return render(request, 'forms/generarserviciovpn.html', {'vpns': vpns})

@login_required
def GenerarServiciosDslamView(request):
    if request.method == "POST":
        print(request.POST)
        ip = request.POST['ip_address'].split(".")[-1]
        outputs = file_generator.generar_output_dslam(vlan=request.POST['vlan'], ip_address=ip)
        
        # Genero el zipFile con los scripts
        zip_buffer = utils.generate_zipFile(outputs=outputs, vlan=request.POST['vlan'])

        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="DSLAM_{request.POST['vlan']}.zip"'
        return response
        
        
    return render(request, 'forms/generarserviciosdslam.html')

@login_required
def GenerarServicioSmtp(request):
    return render(request, 'forms/generarserviciosmtp.html')

@login_required
def GenerarServicioGpsView(request):
    return render(request, 'forms/generarserviciogps.html')

@login_required
def Documentationview(request):
    return render(request, 'documentation.html')

@never_cache
def SignupView(request):
    if request.method == "POST":
        print(request.POST)
        user = authenticate(username=request.POST['nameUser'], password=request.POST['password'])
        
        if user is not None:
            # A backend authenticated the credentials
            login(request, user) # logueamos al usuario 
            
            messages.success(request, "Bienvenido")
            message = {
                'message': 'AUTENTICADO',
                'tags': 'info'
            }
            return redirect('Index')
        else:
            # No backend authenticated the credentials
            message = {
                'message': 'NO EXISTE EL USUARIO',
                'tags': 'danger'
            }
            return render(request, 'login/signup.html',{'message': message})
    if request.user.is_authenticated:
       # messages.get_messages(request).clear()  # Limpia mensajes previos
        messages.info(request, f"{request.user.username} autenticado!") # Mensaje
        return redirect( 'Index')
    return render(request, 'login/signup.html')

@login_required
def LogoutView(request):
    logout(request)
    return redirect('singup')


