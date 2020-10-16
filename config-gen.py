#!/usr/bin/env python

# Este script toma como parametro un path a un archivo de configuracion terraform.tfvars
# Como resultado imprime la configuracion del server DHCP y los comandos de GOVC para controlar el VMware

import os
import re
import subprocess
import sys
import stat
import datetime
import getpass


### NTP servers:
# NOTA: Los NTP se configuran despues mediante el machine config, no se configuran mas por DHCP

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


## Creo mapping entre hostnames y direcciones IP
def hostname_ip_map(hostname_ip):

    for i in range(len(bootstrap_name)):
        hostname_ip[bootstrap_name[i]] = bootstrap_ip[i]

    for i in range(len(control_plane_names)):
        hostname_ip[control_plane_names[i]] = control_plane_ips[i]

    for i in range(len(compute_names)):
        hostname_ip[compute_names[i]] = compute_ips[i]


## Esta funcion obtiene la lista de nodos respetando el node count
def get_nodes():

    nodes = []
    
    nodes.append(bootstrap_name[0])
    
    for i in range(control_plane_count):
        nodes.append(control_plane_names[i])
    
    for i in range(compute_count):
        nodes.append(compute_names[i])
        
    #print(nodes)

    return nodes

## Creo mapping entre nodos y MAC Address
def node_mac_map(node_mac):

    for node in get_nodes():
        govc_proc = subprocess.Popen("govc device.info -vm='/%s/vm/%s/%s' ethernet-0" % (vsphere_datacenter, vm_folder, node), stdout=subprocess.PIPE, shell=True)

        node_mac[node] = "" # "00:00:00:00:00:00"

        for line in iter(govc_proc.stdout.readline, ""):
            #print line
            mac_re = re.search("MAC Address", line)

            if (mac_re):
                mac_address = line.split(": ")[1].strip()
                node_mac[node] = mac_address
                
        if node_mac[node] == "":
            print(bcolors.FAIL + "\n * ERROR * " + bcolors.ENDC + "No se pudo obtener la MAC Address del nodo: " + node)
            print("\nVerifique que las credenciales del usuario para terraform en el archivo terraform.tfvars sean correctas.")
            print("Verifique que las VMs hayan sido creadas ya.\n")
            sys.exit(1)


## Funcion que ejecuta los comandos para establecer los permisos
def ask_and_execute(question, status, command_set):
    print("")

    for command in command_set:
        print(command)

    dialog_input = raw_input("\n" + question + " [y/N]: ")
    if dialog_input != 'y' and dialog_input != 'Y':
        return

    print("\n## " + status)
    print("Se utilizaran las siguientes opciones: ")
    print("vCenter Username: " + os.environ['GOVC_USERNAME']);
    #print("GOVC_PASSWORD = " + os.environ['GOVC_PASSWORD'])
    print("vCenter URL: " + os.environ['GOVC_URL'])
    print("GOVC_INSECURE = " + os.environ['GOVC_INSECURE'])
    
    for command in command_set:
        os.system(command)
    
    print("")


## Generacion de comandos para crear roles y establecer permisos para el usuario de terraform
def permissions_terraform():
    print("\n### Please provide the credentials for the Admin user")
    vsphere_admin_user = raw_input('vCenter Admin User: ')
    vsphere_admin_password = getpass.getpass('vCenter Admin Password: ')
    
    if vsphere_admin_user == "" or vsphere_admin_password == "":
        print("\nNo se ha ingresado el usuario o el password")
        sys.exit(1)
    
    os.environ['GOVC_USERNAME'] = vsphere_admin_user
    os.environ['GOVC_PASSWORD'] = vsphere_admin_password
    os.environ['GOVC_URL'] = vsphere_server
    os.environ['GOVC_INSECURE'] = "1"

    ### Genero los comandos para crear los roles
    add_roles = [ \
'''
## Role creation
# Virtual Network Privileges
govc role.create ocp-terraform-network \\
    Network.Assign

# Low level file operations on the datastore
govc role.create ocp-terraform-datastore \\
    Datastore.AllocateSpace \\
    Datastore.FileManagement 

# StorageProfile.View (Profile-driven storage view) at the vCenter level
govc role.create ocp-terraform-vcenter \\
    StorageProfile.View

# Resource Group Privileges
govc role.create ocp-terraform-resource \\
    Resource.AssignVAppToPool \\
    Resource.AssignVMToPool \\
    Resource.CreatePool \\
    Resource.DeletePool

# Virtual Machine Privileges
govc role.create ocp-terraform-vm \\
    VApp.ApplicationConfig \\
    VApp.Clone \\
    VApp.ExtractOvfEnvironment \\
    VApp.InstanceConfig VApp.ResourceConfig \\
    Folder.Create Folder.Delete \\
    VirtualMachine.Config.AddNewDisk \\
    VirtualMachine.Config.AdvancedConfig \\
    VirtualMachine.Config.CPUCount \\
    VirtualMachine.Config.DiskExtend \\
    VirtualMachine.Config.EditDevice \\
    VirtualMachine.Config.Memory \\
    VirtualMachine.Config.Rename \\
    VirtualMachine.Config.Resource \\
    VirtualMachine.Config.Settings \\
    VirtualMachine.GuestOperations.Execute \\
    VirtualMachine.GuestOperations.Modify \\
    VirtualMachine.GuestOperations.ModifyAliases \\
    VirtualMachine.GuestOperations.Query \\
    VirtualMachine.GuestOperations.QueryAliases \\
    VirtualMachine.Interact.ConsoleInteract \\
    VirtualMachine.Interact.GuestControl \\
    VirtualMachine.Interact.Pause \\
    VirtualMachine.Interact.PowerOff \\
    VirtualMachine.Interact.PowerOn \\
    VirtualMachine.Interact.Reset \\
    VirtualMachine.Interact.SetCDMedia \\
    VirtualMachine.Interact.Suspend \\
    VirtualMachine.Interact.ToolsInstall \\
    VirtualMachine.Inventory.Create \\
    VirtualMachine.Inventory.CreateFromExisting \\
    VirtualMachine.Inventory.Delete \\
    VirtualMachine.Inventory.Move \\
    VirtualMachine.Inventory.Register \\
    VirtualMachine.Inventory.Unregister \\
    VirtualMachine.Provisioning.Clone \\
    VirtualMachine.Provisioning.CloneTemplate \\
    VirtualMachine.Provisioning.CreateTemplateFromVM \\
    VirtualMachine.Provisioning.Customize \\
    VirtualMachine.Provisioning.DeployTemplate \\
    VirtualMachine.Provisioning.DiskRandomAccess \\
    VirtualMachine.Provisioning.DiskRandomRead \\
    VirtualMachine.Provisioning.FileRandomAccess \\
    VirtualMachine.Provisioning.GetVmFiles \\
    VirtualMachine.Provisioning.MarkAsTemplate \\
    VirtualMachine.Provisioning.MarkAsVM \\
    VirtualMachine.Provisioning.ModifyCustSpecs \\
    VirtualMachine.Provisioning.PromoteDisks \\
    VirtualMachine.Provisioning.PutVmFiles \\
    VirtualMachine.Provisioning.ReadCustSpecs
''']

    ask_and_execute("Desea crear los roles?", "Creando roles en vCenter", add_roles)

    ## Busco la carpeta donde esta alojado el template
    govc_find_proc = subprocess.Popen("govc find -type m -name=%s" % (vm_template), shell=True, stdout=subprocess.PIPE)

    vm_template_path = ""

    for line in iter(govc_find_proc.stdout.readline, ""):
        vm_template_path = line.rstrip()
        break

    if vm_template_path == "":
        print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "No se encontro la ruta del template especificado: " + vm_template)
        vm_template_path = "/%s/vm/templates/%s" % (vsphere_datacenter, vm_template)
    else:
        print("Se encontro el template en la ruta: " + vm_template_path)

    govc_find_proc.stdout.close()

    ## Busco el nombre del Resource Pool
    govc_find_proc = subprocess.Popen("for ResourcePool in $(govc find / -type p); do govc ls -l -i $ResourcePool; done", shell=True, stdout=subprocess.PIPE)

    vm_resource_pool = ""

    for line in iter(govc_find_proc.stdout.readline, ""):
        if line.find(vm_resource_pool_id) != -1:
            #vm_resource_pool = line.rstrip()
            #print(line.rstrip())
            vm_resource_pool = line.rstrip().split(" ")[1]

    if vm_resource_pool == "":
        print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "No se encontro el resource pool asociado al ID especificado: " + vm_resource_pool_id)
        vm_resource_pool = "/%s/host/%s/Resources/ocp-resource" % (vsphere_datacenter, vsphere_cluster)
    else:
        print("Se encontro el resource group en la ruta: " + vm_resource_pool)

    govc_find_proc.stdout.close()

    ### Genero los comandos para establecer los permisos
    set_permissions = [ \
        "govc permissions.set -principal %s -role ocp-terraform-vm -propagate=true '/%s/vm/%s'" % (vsphere_user, vsphere_datacenter, vm_folder), \
        "govc permissions.set -principal %s -role ocp-terraform-vm -propagate=false '%s'" % (vsphere_user, vm_template_path), \
        "govc permissions.set -principal %s -role ocp-terraform-network -propagate=false '/%s/network/%s'" % (vsphere_user, vsphere_datacenter, vm_network), \
        "govc permissions.set -principal %s -role ocp-terraform-datastore -propagate=false '/%s/datastore/%s'" % (vsphere_user, vsphere_datacenter, vsphere_datastore), \
        "govc permissions.set -principal %s -role ocp-terraform-resource -propagate=false '%s'" % (vsphere_user, vm_resource_pool), \
        "govc permissions.set -principal %s -role ocp-terraform-vcenter -propagate=false '/'" % (vsphere_user)]

    ask_and_execute("Desea establecer los permisos?", "Set permissions on vCenter objects", set_permissions)
        
    ### Genero los comandos para quitar los permisos
    del_permissions = [ \
        "govc permissions.remove -principal %s '/%s/vm/%s'" % (vsphere_user, vsphere_datacenter, vm_folder), 
        "govc permissions.remove -principal %s '%s'" % (vsphere_user, vm_template_path), 
        "govc permissions.remove -principal %s '/%s/network/%s'" % (vsphere_user, vsphere_datacenter, vm_network), 
        "govc permissions.remove -principal %s '/%s/datastore/%s'" % (vsphere_user, vsphere_datacenter, vsphere_datastore), 
        "govc permissions.remove -principal %s '%s'" % (vsphere_user, vm_resource_pool), 
        "govc permissions.remove -principal %s '/'" % (vsphere_user)]

    ask_and_execute("Desea quitar los permisos?", "Remove permissions from vCenter objects", del_permissions)

    ### Genero los comandos para eliminar los roles
    del_roles = [ \
        "govc role.remove ocp-terraform-vm", \
        "govc role.remove ocp-terraform-network", \
        "govc role.remove ocp-terraform-datastore", \
        "govc role.remove ocp-terraform-resource", \
        "govc role.remove ocp-terraform-vcenter"]

    ask_and_execute("Desea eliminar los roles?", "Remove vCenter roles", del_roles)


def permissions_dynamic_provisioning():
    print("\n### Please provide the following data for Dynamic Provisioning")
    dynamic_provisioning_user = raw_input('Dynamic Provisioning User: ')
    dynamic_provisioning_datastore = raw_input('Dynamic Provisioning Datastore: ')
    #dynamic_provisioning_host = raw_input('Dynamic Provisioning ESXi host: ')

    ### Genero los comandos para crear los roles
    add_roles = [ \
'''
## Role creation
# StorageProfile.View (Profile-driven storage view) at the vCenter level
govc role.create k8s-system-read-and-spbm-profile-view \\
    StorageProfile.View

# Low level file operations on the datastore
govc role.create manage-k8s-volumes \\
    Datastore.AllocateSpace \\
    Datastore.FileManagement

# Virtual Machine Privileges
govc role.create manage-k8s-node-vms \\
    Resource.AssignVMToPool \\
    VirtualMachine.Config.AddExistingDisk \\
    VirtualMachine.Config.AddNewDisk \\
    VirtualMachine.Config.AddRemoveDevice \\
    VirtualMachine.Config.RemoveDisk \\
    VirtualMachine.Inventory.Create \\
    VirtualMachine.Inventory.Delete \\
    VirtualMachine.Config.Settings
''']
    
    ask_and_execute("Desea crear los roles?", "Creando roles en vCenter", add_roles)

    ### Genero los comandos para establecer los permisos
    #    "govc permissions.set -principal %s -role ReadOnly -propagate=false '/%s/host/%s'" % (dynamic_provisioning_user, vsphere_datacenter, dynamic_provisioning_host), \
    #    "govc permissions.set -principal %s -role manage-k8s-node-vms -propagate=true /%s/host/%s" % (dynamic_provisioning_user, vsphere_datacenter, dynamic_provisioning_host), \
    set_permissions = [ \
        "govc permissions.set -principal %s -role ReadOnly -propagate=false '/%s'" % (dynamic_provisioning_user, vsphere_datacenter), \
        "govc permissions.set -principal %s -role ReadOnly -propagate=false '/%s/datastore/%s'" % (dynamic_provisioning_user, vsphere_datacenter, dynamic_provisioning_datastore), \
        "govc permissions.set -principal %s -role ReadOnly -propagate=false '/%s/vm/%s'" % (dynamic_provisioning_user, vsphere_datacenter, vm_folder), \

        "govc permissions.set -principal %s -role k8s-system-read-and-spbm-profile-view -propagate=false /" % (dynamic_provisioning_user), \
        "govc permissions.set -principal %s -role manage-k8s-volumes -propagate=false /%s/datastore/%s" % (dynamic_provisioning_user, vsphere_datacenter, dynamic_provisioning_datastore), \
        "govc permissions.set -principal %s -role manage-k8s-node-vms -propagate=true /%s/vm/%s" % (dynamic_provisioning_user, vsphere_datacenter, vm_folder)]

    ask_and_execute("Desea establecer los permisos?", "Set Dynamic Provisioning permissions for vCenter objects", set_permissions)

    ### Genero los comandos para quitar los permisos
    #    "govc permissions.remove -principal %s '/%s/host/%s'" % (vsphere_user, vsphere_datacenter, dynamic_provisioning_host), \
    del_permissions = [ \
        "govc permissions.remove -principal %s '/'" % (vsphere_user), \
        "govc permissions.remove -principal %s '/%s/datastore/%s'" % (vsphere_user, vsphere_datacenter, vsphere_datastore), \
        "govc permissions.remove -principal %s '/%s/vm/%s'" % (vsphere_user, vsphere_datacenter, vm_folder)]

    ask_and_execute("Desea quitar los permisos?", "Remove Dynamic Provisioning permissions from vCenter objects", del_permissions)

    ### Genero los comandos para eliminar los roles
    del_roles = [ \
        "govc role.remove k8s-system-read-and-spbm-profile-view", \
        "govc role.remove manage-k8s-volumes", \
        "govc role.remove manage-k8s-node-vms"]

    ask_and_execute("Desea eliminar los roles?", "Remove Dynamic Provisioning roles", del_roles)


## Esta funcion apaga y enciende las VMs
def power():
    ### Genero los comandos para apagar las VMs
    shutdown_commands = []
    for node in get_nodes():
        shutdown_commands.append("govc vm.power -off /%s/vm/%s/%s" % (vsphere_datacenter, vm_folder, node))

    ask_and_execute("Desea apagar las VMs creadas?", "Apagado de las VMs creadas", shutdown_commands)

    ### Genero los comandos para encender las VMs
    startup_commands = []
    for node in get_nodes():
        startup_commands.append("govc vm.power -on /%s/vm/%s/%s" % (vsphere_datacenter, vm_folder, node))

    ask_and_execute("Desea encender las VMs creadas?", "Encendido de las VMs creadas", startup_commands)


## Esta funcion muestra los comandos para fijar las MAC Address actuales
def mac_address():
    # Obtengo los mappings de node <-> MAC Address
    node_mac = {}
    node_mac_map(node_mac)

    ### Genero los comandos para setar las MAC Address
    print("\n## Setear MAC addressess")
    for node in node_mac:
        print ("govc vm.network.change -vm /%s/vm/%s/%s -net '%s' -net.address %s ethernet-0" % (vsphere_datacenter, vm_folder, node, vm_network, node_mac[node]))


## Esta funcion valida la consulta de DNS directa
def dns_forward(hostname, ip, server):
    dig_cmd = "dig %s +short" % (hostname) + " @" + server
    
    dig_proc = subprocess.Popen(dig_cmd, stdout=subprocess.PIPE, shell=True)

    found = False

    print (dig_cmd + " <=> " + ip)

    for line in iter(dig_proc.stdout.readline, ""):
        if line.strip() == ip:
          found = True

    if found == False:
        print (bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "Fallo la verificacion de DNS del host: " + hostname)
        print ("DNS Server: " + server)
        sys.exit(1)


## Esta funcion realiza una validacion basica de la consulta de DNS directa
def dns_check(hostname, server):
    dig_cmd = "dig %s +short" % (hostname) + " @" + server
    
    dig_proc = subprocess.Popen(dig_cmd, stdout=subprocess.PIPE, shell=True)

    found = False

    print (dig_cmd)

    for line in iter(dig_proc.stdout.readline, ""):
        print(line.strip())
        found = True

    if found == False:
        print (bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "Fallo la verificacion de DNS del host: " + hostname)
        print ("DNS Server: " + server)
        sys.exit(1)


## Esta funcion valida la consulta de DNS reversa
def dns_reverse(hostname, ip, server, condition):
    digx_cmd = "dig -x %s +short" % (ip) + " @" + server

    digx_proc = subprocess.Popen(digx_cmd, stdout=subprocess.PIPE, shell=True)

    found = False

    print (digx_cmd + " <=> " + hostname)

    for line in iter(digx_proc.stdout.readline, ""):
        if hostname in line.strip():
          found = True

    if found != condition:
        print (bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "Fallo la verificacion de DNS *reverso* del host: " + hostname)
        print ("DNS Server: " + server)
        if condition == False:
            print("Los registros etcd no deben tener un reverso configurado")
        sys.exit(1)


### Verificar que los registros DNS esten bien
def dns_records():
    # Obtengo los mappings de hostname <-> IP
    hostname_ip = {}
    hostname_ip_map(hostname_ip)

    print("\n## Verificando registros DNS")

    for dns_ip in dns_ips:
        print("\n## Verificacion de registros de los nodos")
        for node in get_nodes():
            dns_forward(node + "." + cluster_domain, hostname_ip[node], dns_ip)
            dns_reverse(node + "." + cluster_domain, hostname_ip[node], dns_ip, True)

        print("\n## Verificacion de registros etcd")
        for i in range(len(control_plane_names)):
            dns_forward("etcd-%s.%s" % (i, cluster_domain), hostname_ip[control_plane_names[i]], dns_ip)
            dns_reverse("etcd-%s.%s" % (i, cluster_domain), hostname_ip[control_plane_names[i]], dns_ip, False)
            
        print (bcolors.OKGREEN + "\n * OK * " + bcolors.ENDC + "Registros DNS A y reverso (server: " + dns_ip + ")\n")
        
        # Verificacion de APIs
        print("\n## Verificacion de APIs")
        dns_check("api." + cluster_domain, dns_ip)
        dns_check("api-int." + cluster_domain, dns_ip)
        dns_check("*.apps." + cluster_domain, dns_ip)

        # Verificacion de registros SRV
        print("\n## Verificacion de registros SRV")

        dig_cmd = "dig _etcd-server-ssl._tcp.%s SRV +short" % cluster_domain + " @" + dns_ip
        print (dig_cmd)
        os.system(dig_cmd)


### Genero la configuracion del server DHCP
def dhcp_server():
    # Obtengo los mappings de hostname <-> IP
    hostname_ip = {}
    hostname_ip_map(hostname_ip)

    # Obtengo los mappings de node <-> MAC Address
    node_mac = {}
    node_mac_map(node_mac)

    # Grabar un archivo dhpcd.conf y mostrar el comando para copiarlo a /etc + start/stop/enable del dhpcd + yum install (suponer que arrancamos de 0) + echo "" > /var/lib/dhpcd/lease
    print("\n## Configurando y levantando el DHCP server")

    # Crear un archivo de configuracion /etc/dhcp/dhcpd.conf con las MAC Address
    dhcpd_file = os.open("dhcpd.conf", os.O_WRONLY | os.O_CREAT | os.O_TRUNC)

    # Obtengo la subred y la mascara
    def cidr_to_netmask(cidr):
      cidr = int(cidr)
      mask = (0xffffffff >> (32 - cidr)) << (32 - cidr)
      return (str( (0xff000000 & mask) >> 24)   + '.' +
              str( (0x00ff0000 & mask) >> 16)   + '.' +
              str( (0x0000ff00 & mask) >> 8)    + '.' +
              str( (0x000000ff & mask)))

    subnet = machine_cidr.split("/")[0]
    cidr = machine_cidr.split("/")[1]

    netmask = cidr_to_netmask(cidr)

    dhcpd_conf_general = \
    '''
# dhcpd.conf
# Generated by: config-gen.py

option domain-name "%s";
option domain-name-servers %s, %s, %s;

default-lease-time 600;
max-lease-time 7200;

# Use this to send dhcp log messages to a different log file (you also
# have to hack syslog.conf to complete the redirection).
log-facility local7;

subnet %s netmask %s {
    option routers %s;
}
    ''' % (cluster_domain, dns_ips[0], dns_ips[1], dns_ips[2], subnet, netmask, gateway_ip)

    dhcpd_conf_hosts = ""

    for node in get_nodes():
        dhcpd_conf_hosts += \
        '''
host %s {
  hardware ethernet %s;
  option host-name "%s";
  fixed-address %s;
}
        ''' % (node, node_mac[node], node + "." + cluster_domain, hostname_ip[node])

    # Concatenar secciones y grabar el archivo
    dhcpd_conf = dhcpd_conf_general + dhcpd_conf_hosts + "\n"
    ret = os.write(dhcpd_file, dhcpd_conf)
    os.close(dhcpd_file)
    os.chmod("dhcpd.conf", stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    
    # Hacer backup del archivo dhcpd.conf
    # Copiar el archivo generado a /etc/dhcp/dhcpd.conf (\ es para evitar el alias: cp='cp -i')
    # Detener el dhcpd
    # Borrar los leases
    # Iniciar el dhcpd
    # Mostrar el status
    dhcp_commands = [ \
        "cp /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf-" + datetime.datetime.now().strftime("%Y%m%d%M%S"), \
        "\cp dhcpd.conf /etc/dhcp/dhcpd.conf", \
        "systemctl stop dhcpd", \
        "echo '' > /var/lib/dhcpd/dhcpd.leases", \
        "echo '' > /var/lib/dhcpd/dhcpd.leases~", \
        "systemctl start dhcpd", \
        "systemctl status dhcpd"]   
        
    for command in dhcp_commands:
        print(command)
        os.system(command)


### Funcion prepara los archivos ignition
def prepare_ignition():
    install_dir = raw_input("\nIngrese la ruta absoluta del directorio que contiene los ignition files (ej: /root/ocp4): ")
    
    if install_dir == "":
        print("\nAdios!")
        sys.exit(1)
    
    #html_dir = raw_input("\nIngrese la ruta absoluta del directorio que contiene los ignition files (ej: /root/ocp4): ")
    
    #que copie el bootstrap.ign a un directorio de html (preguntar) // master.ign y worker.ign los ponga en el tfvars

    filename = sys.argv[2]

    input_file = open(filename, "r")

    master_ignition = open(install_dir + "/master.ign", "r")
    worker_ignition = open(install_dir + "/worker.ign", "r")
    
    output_file = open(filename + "~", "w")

    print("\n## Procesando archivo: " + filename)
    
    output = True

    for line in input_file:
        if line.find("control_plane_ignition") != -1:
            output_file.write(line)
            for master_line in master_ignition:
                output_file.write(master_line)
                output_file.write("\n")
            output = False
        
        if line.find("compute_ignition") != -1:
            output_file.write(line)
            for worker_line in worker_ignition:
                output_file.write(worker_line)
                output_file.write("\n")
            output = False
        
        #print(line.find("END_OF_MASTER_IGNITION"))
        
        if line.find("END_OF_MASTER_IGNITION") == 0 or line.find("END_OF_WORKER_IGNITION") == 0:
            output = True
            
        if output == True:
            output_file.write(line)
    
    input_file.close()
    master_ignition.close()
    worker_ignition.close()
    output_file.close()
    
    os.system("\mv " + filename + "~ " + filename)



### Verficar que me hayan pasado los parametros correctos
if len(sys.argv) != 3:
    print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "Cantidad de parametros incorrecta")
    print('''
USO: config-gen.py seccion terraform.tfvars
Secciones:
 - perms (Muestra los comandos de govc para gestionar los permisos del usuario de terraform)
 - power (Muestra los comandos de govc para encender y apagar las VMs)
 - mac   (Muestra los comandos de govc para fijar las MAC Address)
 - dns   (Valida las entradas DNS)
 - ign   (Pega el contenido de los archivos master.ign y worker.ign en el archivo tfvars)
 - dhcp  (Genera la configuracion de un DHCP server [dhcpd])
''')
    sys.exit(1)

### Validar prerequisitos: terraform, govc, dig, dhcpd
print ("\n## Validando prerequisitos: terraform, govc, dig, dhcpd")
for cmd in ["terraform", "govc", "dig", "dhcpd"]:
    if os.system("which " + cmd) != 0:
        print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "El comando: " + cmd + " no se encuentra instalado")
        sys.exit(1)


### Proceso el archivo leyendo las variables del mismo, por suerte el formato de variables de terraform es igual al de python
filename = sys.argv[2]

terraform_file = open(filename, "r")

print("\n## Procesando archivo: " + filename)

for line in terraform_file:
    #print(line)

    comment = re.search("^//", line)
    control_plane_ignition = re.search("END_OF_MASTER_IGNITION", line)
    compute_ignition = re.search("END_OF_WORKER_IGNITION", line)

    if (comment or control_plane_ignition or compute_ignition):
      continue

    exec(line)


### Verifico que el cluster domain contiene el cluster_id
print("\n## Verificando cluster domain: " + cluster_domain)
if cluster_domain.find(cluster_id) == -1:
    print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "El cluster domain esta mal configurado, no contiene el nombre del cluster: " + cluster_id)
    sys.exit(1)
    

### Verifico que la carpeta tenga el nombre del cluster
print("\n## Verificando carpeta: " + vm_folder)
if os.path.basename(vm_folder) != cluster_id:
    print(bcolors.FAIL + " * ERROR * " + bcolors.ENDC + "La carpeta de VMs debe tener el mismo nombre que el cluster: " + cluster_id)
    print("ATENCION! Si no se respeta esta norma, entonces fallara el Dynamic Provisioning")
    sys.exit(1)


## Establezco por default el entorno de govc con el usuario de terraform
os.environ['GOVC_URL'] = vsphere_server
os.environ['GOVC_INSECURE'] = "1"

os.environ['GOVC_USERNAME'] = vsphere_user
os.environ['GOVC_PASSWORD'] = vsphere_password

section = sys.argv[1]

if section == "perms":
    dialog_input = raw_input("\nDesea configurar los permisos del usuario de Terraform [y/N]: ")
    if dialog_input == 'y' or dialog_input == 'Y':
        permissions_terraform()

    dialog_input = raw_input("\nDesea configurar los permisos del usuario de Dynamic Provisioning [y/N]: ")
    if dialog_input == 'y' or dialog_input == 'Y':
        permissions_dynamic_provisioning()
    
    ## Finalmente limpio el username y password para que no quede en memoria
    os.environ['GOVC_USERNAME'] = ""
    os.environ['GOVC_PASSWORD'] = ""

elif section == "power":
    power()

elif section == "mac":
    mac_address()

elif section == "dns":
    dns_records()

elif section == "dhcp":
    dhcp_server()

elif section == "ign":
    prepare_ignition()



