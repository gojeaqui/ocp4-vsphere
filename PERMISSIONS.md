## Required Privileges (terraform)

In order to use Terraform provider as non priviledged user, some Roles within vCenter must be assigned the following privileges:

- Datastore (Role: ocp-terraform-datastore)
  - Allocate space
  - Low level file operations
- Profile-driven storage (Role: ocp-terraform-vcenter)
  - Profile-driven storage view
- Network (Role: ocp-terraform-network)
  - Assign network
- Resource (Role: ocp-terraform-resource)
  - Assign vApp to resource pool
  - Assign virtual machine to resource pool
- vApp (Role: ocp-terraform-vm)
  - Clone
  - View OVF environment
  - vApp application configuration
  - vApp instance configuration
  - vApp resource configuration
- Virtual machine (Role: ocp-terraform-vm)
  - Change Configuration (all)
  - Edit Inventory (all)
  - Guest operations (all)
  - Interaction (all)
  - Provisioning (all)

And these roles have to be given permission on the following entities:
Role | Entity | Propagate to Children | Description
---- | ------ | --------- | -----------
ocp-terraform-vm | VM Folder | Yes | The folder where VMs will be alocated
ocp-terraform-vm | Virtual Machine | No | The OVA template that will be cloned
ocp-terraform-network | VM Network | No | The VM Network the VMs will attach  to
ocp-terraform-datastore | Datastore | No | The Datastore where the VMs disk0 will reside
ocp-terraform-resource | Resource Pool |  No | The Resource Pool the VMs will we added to
ocp-terraform-vcenter | vCenter | No | Profile-driven storage view
Read-Only (System) | Virtual Switch | No | The Distributed Virtual Switch (\*)

(\*) If the VM Network is going to be on a Distributed Virtual Switch then this permissions needs to be applied as well

Command line example:
```
# CLI Role creation
govc role.create ocp-terraform-network Network.Assign
govc role.create ocp-terraform-datastore Datastore.AllocateSpace Datastore.FileManagement 
govc role.create ocp-terraform-vcenter StorageProfile.View
govc role.create ocp-terraform-resource Resource.AssignVAppToPool Resource.AssignVMToPool
govc role.create ocp-terraform-vm \
	VApp.ApplicationConfig VApp.Clone VApp.ExtractOvfEnvironment VApp.InstanceConfig VApp.ResourceConfig \
	Folder.Create Folder.Delete \
	VirtualMachine.Config.AddNewDisk VirtualMachine.Config.AdvancedConfig VirtualMachine.Config.CPUCount \
	VirtualMachine.Config.DiskExtend VirtualMachine.Config.EditDevice VirtualMachine.Config.Memory \
	VirtualMachine.Config.Rename VirtualMachine.Config.Resource VirtualMachine.Config.Settings \
	VirtualMachine.GuestOperations.Execute VirtualMachine.GuestOperations.Modify VirtualMachine.GuestOperations.ModifyAliases \
	VirtualMachine.GuestOperations.Query VirtualMachine.GuestOperations.QueryAliases \
	VirtualMachine.Interact.ConsoleInteract VirtualMachine.Interact.GuestControl VirtualMachine.Interact.Pause \
	VirtualMachine.Interact.PowerOff VirtualMachine.Interact.PowerOn VirtualMachine.Interact.Reset \
	VirtualMachine.Interact.SetCDMedia VirtualMachine.Interact.Suspend VirtualMachine.Interact.ToolsInstall \
	VirtualMachine.Inventory.Create VirtualMachine.Inventory.CreateFromExisting VirtualMachine.Inventory.Delete \
	VirtualMachine.Inventory.Move VirtualMachine.Inventory.Register VirtualMachine.Inventory.Unregister \
	VirtualMachine.Provisioning.Clone VirtualMachine.Provisioning.CloneTemplate VirtualMachine.Provisioning.CreateTemplateFromVM \
	VirtualMachine.Provisioning.Customize VirtualMachine.Provisioning.DeployTemplate VirtualMachine.Provisioning.DiskRandomAccess \
	VirtualMachine.Provisioning.DiskRandomRead VirtualMachine.Provisioning.FileRandomAccess VirtualMachine.Provisioning.GetVmFiles \
	VirtualMachine.Provisioning.MarkAsTemplate VirtualMachine.Provisioning.MarkAsVM VirtualMachine.Provisioning.ModifyCustSpecs \
	VirtualMachine.Provisioning.PromoteDisks VirtualMachine.Provisioning.PutVmFiles VirtualMachine.Provisioning.ReadCustSpecs

# CLI Permissions set
$USER = "ocp-terraform@vsphere.local"
$FOLDER = "openshift/ocp"
$DATACENTER = "Datacenter"
$DATASTORE = "Datastore"
$NETWORK = "VM Network"
$RESOURCE = "openshift"
govc permissions.set -principal $USER -role ocp-terraform-vm -propagate=true "/$DATACENTER/vm/$FOLDER"
govc permissions.set -principal $USER -role ocp-terraform-vm -propagate=false "/$DATACENTER/vm/templates/rhcos"
govc permissions.set -principal $USER -role ocp-terraform-network -propagate=false "/$DATACENTER/network/$NETWORK"
govc permissions.set -principal $USER -role ocp-terraform-datastore -propagate=false "/$DATACENTER/datastore/$DATASTORE"
govc permissions.set -principal $USER -role ocp-terraform-resource -propagate=false "/$DATACENTER/host/Cluster/Resources/$RESOURCE"
govc permissions.set -principal $USER -role ocp-terraform-vcenter -propagate=false "/"
```

The config-gen.py script generates the commands needed to create these roles and assign them to the corresponding vCenter objects.

These settings have been tested with:
- [vSphere 6.7](https://pubs.vmware.com/vsphere-60/index.jsp?topic=%2Fcom.vmware.vsphere.security.doc%2FGUID-18071E9A-EED1-4968-8D51-E0B4F526FDA3.html)
- [vSphere 6.0](https://pubs.vmware.com/vsphere-60/index.jsp?topic=%2Fcom.vmware.vsphere.security.doc%2FGUID-18071E9A-EED1-4968-8D51-E0B4F526FDA3.html)
- [vSphere 5.5](https://pubs.vmware.com/vsphere-55/index.jsp?topic=%2Fcom.vmware.vsphere.security.doc%2FGUID-18071E9A-EED1-4968-8D51-E0B4F526FDA3.html). 

## Required Privileges (dynamic provisioning)
[Permissions | vSphere Storage for Kubernetes](https://vmware.github.io/vsphere-storage-for-kubernetes/documentation/vcp-roles.html)

Command line example:
```
# CLI Role creation

# StorageProfile.View (Profile-driven storage view) at the vCenter level
govc role.create k8s-system-read-and-spbm-profile-view StorageProfile.View

# Low level file operations on the datastore
govc role.create manage-k8s-volumes Datastore.AllocateSpace Datastore.FileManagement

# Virtual Machine Privileges
govc role.create manage-k8s-node-vms \
	Resource.AssignVMToPool \
	VirtualMachine.Config.AddExistingDisk \
	VirtualMachine.Config.AddNewDisk \
	VirtualMachine.Config.AddRemoveDevice \
	VirtualMachine.Config.RemoveDisk \
	VirtualMachine.Inventory.Create \
	VirtualMachine.Inventory.Delete \
	VirtualMachine.Config.Settings

# CLI Permissions set
$USER = "ocp-dynamic-provisioning@vsphere.local"
$FOLDER = "openshift/ocp"
$DATACENTER = "Datacenter"
$DATASTORE = "Datastore"
$NETWORK = "VM Network"

# Read-only permissions
govc permissions.set -principal $USER -role ReadOnly -propagate=false "/$DATACENTER"
govc permissions.set -principal $USER -role ReadOnly -propagate=false "/$DATACENTER/datastore/$DATASTORE"
govc permissions.set -principal $USER -role ReadOnly -propagate=false "/$DATACENTER/host/$HOST"
govc permissions.set -principal $USER -role ReadOnly -propagate=false "/$DATACENTER/vm/$FOLDER"
govc permissions.set -principal $USER -role ReadOnly -propagate=false "/$DATACENTER/network/$NETWORK"

govc permissions.set -principal $USER -role k8s-system-read-and-spbm-profile-view -propagate=false
govc permissions.set -principal $USER -role manage-k8s-volumes -propagate=false /$DATACENTER/datastore/$DATASTORE
govc permissions.set -principal $USER -role manage-k8s-node-vms -propagate=true /$DATACENTER/host/$HOST
govc permissions.set -principal $USER -role manage-k8s-node-vms -propagate=true /$DATACENTER/vm/$FOLDER
```

For additional information on roles and permissions, please refer to official VMware documentation:
- [Managing Permissions for vCenter Components](https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-3B78EEB3-23E2-4CEB-9FBD-E432B606011A.html)
- [Required Privileges for Common Tasks](https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-4D0F8E63-2961-4B71-B365-BBFA24673FDB.html)
- [Using Roles to Assign Privileges](https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-18071E9A-EED1-4968-8D51-E0B4F526FDA3.html)
- [Defined Privileges](https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-ED56F3C4-77D0-49E3-88B6-B99B8B437B62.html)
