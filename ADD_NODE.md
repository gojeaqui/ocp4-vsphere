# Adding Cluster nodes after installation

https://docs.openshift.com/container-platform/4.3/installing/installing_vsphere/installing-vsphere.html#installation-approve-csrs_installing-vsphere

Once the Cluster has been installed and is in production you have to be careful with terraform apply, because if there is Dynamic Provisioning in use then some disks might be attached to Cluster nodes that terraform does not know about.

To deal with the drift caused by the Dynamic Provisioning the strategy is to use the terraform apply -target option.

## Creating the node with terraform
First add the new node the terraform.tfvars configuration file also increasing the node count.

### Terraform manual process:
Check the terraform state to get the name of the target for the next node that you want to add.

Example:
```
[root@bastion ~]# terraform state list | grep virtual_machine.vm
module.compute.vsphere_virtual_machine.vm[0]
module.compute.vsphere_virtual_machine.vm[1]
module.control_plane.vsphere_virtual_machine.vm[0]
module.control_plane.vsphere_virtual_machine.vm[1]
module.control_plane.vsphere_virtual_machine.vm[2]
```

So, in order to add a 3rd worker node execute this terraform apply:
```
terraform apply -target=module.compute.vsphere_virtual_machine.vm[2]
```

Remember to add the new node(s) to the DHCP server.

### Terraform automatic process:
Run config-gen.py add terraform.tfvars and follow the prompts, it will give you the terraform apply command to run

## Adding the created node
Wait until the node gets to the login prompt

Check to see if there are CSRs to approve
```
[root@bastion ~]# oc get csr
NAME        AGE     REQUESTOR                                                                   CONDITION
csr-f4vdb   2m53s   system:serviceaccount:openshift-machine-config-operator:node-bootstrapper   Pending
csr-hkhsh   16m     system:node:infra-0.ocp4.example.com                                        Approved,Issued
csr-kcp9g   15m     system:node:infra-0.ocp4.example.com                                        Approved,Issued
csr-kt6sb   55m     system:node:master-1.ocp4.example.com                                       Approved,Issued
csr-zvblm   42m     system:node:master-2.ocp4.example.com                                       Approved,Issued
```

Aprobe the CSRs
```
[root@bastion ~]# oc adm certificate approve csr-f4vdb
```

Check again, the first time the node appears as: "system:serviceaccount:openshift-machine-config-operator:node-bootstrapper"
```
[root@bastion html]# oc get csr
NAME        AGE     REQUESTOR                                                                   CONDITION
csr-9dg9f   79m     system:node:master-2.ocp4.example.com                                       Approved,Issued
csr-9f7hx   25s     system:node:worker-0.ocp4.example.com                                       Pending
csr-bkv6s   111m    system:node:infra-2.ocp4.example.com                                        Approved,Issued
...
```

If there are many CSR there is a faster way to approve them all:
```
oc get csr -o go-template='{{range .items}}{{if not .status}}{{.metadata.name}}{{"\n"}}{{end}}{{end}}' | xargs oc adm certificate approve
```

Check the pods being created on the new nodes
```
[root@bastion html]# oc get pods -A -o wide | grep worker-0
openshift-cluster-node-tuning-operator tuned-nkshd          0/1  ContainerCreating   0    4m50s   10.76.54.191   worker-0.ocp4.example.com
openshift-monitoring                   node-exporter-jzhq9  0/2  Init:0/1            0    4m50s   10.76.54.191   worker-0.ocp4.example.com
openshift-multus                       multus-8hfcr         0/1  Init:0/5            0    4m50s   10.76.54.191   worker-0.ocp4.example.com
openshift-sdn                          ovs-2l7wf            0/1  ContainerCreating   0    4m50s   10.76.54.191   worker-0.ocp4.example.com
openshift-sdn                          sdn-2x5vd            0/1  Init:0/1            0    4m50s   10.76.54.191   worker-0.ocp4.example.com
```

Check that the node gets addedd to the list of nodes
```
[root@bastion ~]# oc get nodes
NAME                                STATUS     ROLES    AGE   VERSION
infra-0.ocp4.example.com            Ready      worker   17h   v1.16.2
infra-1.ocp4.example.com            Ready      worker   17h   v1.16.2
infra-2.ocp4.example.com            NotReady   worker   7s    v1.16.2
master-0.ocp4.example.com           Ready      master   17h   v1.16.2
master-1.ocp4.example.com           Ready      master   17h   v1.16.2
master-2.ocp4.example.com           Ready      master   17h   v1.16.2
```

Eventually the node is restarted and addedd to the cluster in the "Ready" state
```
[root@bastion ~]# oc get nodes
NAME                                STATUS   ROLES    AGE     VERSION
infra-0.ocp4.example.com            Ready    worker   17h     v1.16.2
infra-1.ocp4.example.com            Ready    worker   17h     v1.16.2
infra-2.ocp4.example.com            Ready    worker   2m13s   v1.16.2
master-0.ocp4.example.com           Ready    master   17h     v1.16.2
master-1.ocp4.example.com           Ready    master   17h     v1.16.2
master-2.ocp4.example.com           Ready    master   17h     v1.16.2
```

If the new node was and infra node, it is necessary to tag it as such:
```
oc label node infra-2.ocp4.example.com node-role.kubernetes.io/infra=""
```

And remove the worker tag:
```
oc label node infra-2.ocp4.example.com node-role.kubernetes.io/worker-
```

Verify that the new nodes are tagged as infra and not worker:
```
oc get nodes
```

