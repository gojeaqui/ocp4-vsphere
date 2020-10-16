# Deleting Cluster nodes after installation

https://docs.openshift.com/container-platform/3.11/admin_guide/manage_nodes.html#deleting-nodes

Once the Cluster has been installed and is in production you have to be careful with terraform apply, because if there is Dynamic Provisioning in use then some disks might be attached to Cluster nodes that terraform does not know about.

To deal with the drift caused by the Dynamic Provisioning the strategy is to use the terraform apply -target option.

### List the nodes in the OpenShift Cluster
```
[openshift@bastion ~]$ oc get nodes
NAME                         STATUS   ROLES    AGE   VERSION
master-0.ocp4.example.com    Ready    master   8d    v1.16.2
master-1.ocp4.example.com    Ready    master   8d    v1.16.2
master-2.ocp4.example.com    Ready    master   8d    v1.16.2
infra-0.ocp4.example.com     Ready    infra    8d    v1.16.2
infra-1.ocp4.example.com     Ready    infra    8d    v1.16.2
infra-2.ocp4.example.com     Ready    infra    8d    v1.16.2
worker-0.ocp4.example.com    Ready    worker   8d    v1.16.2
worker-1.ocp4.example.com    Ready    worker   8d    v1.16.2
worker-2.ocp4.example.com    Ready    worker   8d    v1.16.2
```

### Remove the node from the OpenShift Cluster
```
[root@bastion ~]$ oc delete node worker-2.ocp4.example.com
```

After running this command you can remove the node through VMWare or through terraform

### Terraform manual process:
Check the terraform state to get the name of the target for the node that you want to remove.

Example:
```
[root@bastion ~]$ terraform state list | grep virtual_machine.vm
module.compute.vsphere_virtual_machine.vm[0]
module.compute.vsphere_virtual_machine.vm[1]
module.control_plane.vsphere_virtual_machine.vm[0]
module.control_plane.vsphere_virtual_machine.vm[1]
module.control_plane.vsphere_virtual_machine.vm[2]
```

So, in order to remove the 3rd worker node execute this terraform destroy:
```
terraform destroy -target=module.compute.vsphere_virtual_machine.vm[2]
```

