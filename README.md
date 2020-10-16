# Reference Documentation:
 * [Deploying a User Provisioned Infrastructure environment for OpenShift 4.1 on vSphere](https://blog.openshift.com/deploying-a-user-provisioned-infrastructure-environment-for-openshift-4-1-on-vsphere/)
 * [OpenShift 4.2 vSphere Install Quickstart](https://blog.openshift.com/openshift-4-2-vsphere-install-quickstart/)
 * [Installing a cluster on vSphere](https://docs.openshift.com/container-platform/4.3/installing/installing_vsphere/installing-vsphere.html)
 * [OpenShift 4.3 installation on VMware vSphere with static IPs](https://labs.consol.de/container/platform/openshift/2020/01/31/ocp43-installation-vmware.html)

# Pre-Requisites

* [terraform version 0.11.14](https://releases.hashicorp.com/terraform/0.11.14)
* [VMWare command line tool govc](https://github.com/vmware/govmomi)

# Setup Prerequisites
Install the required packages
```
yum install -y bind-utils httpd dhcp-server unzip git
```

Download the terraform executable and install it
```
curl -O https://releases.hashicorp.com/terraform/0.11.14/terraform_0.11.14_linux_amd64.zip
unzip terraform_0.11.14_linux_amd64.zip
cp terraform /usr/local/bin
```

Validate version (should be: v0.11.14)
```
terraform version
```

Download and install VMware CLI
```
curl -L https://github.com/vmware/govmomi/releases/download/v0.20.0/govc_linux_amd64.gz > govc_0.20.0_linux_amd64.gz
gunzip govc_0.20.0_linux_amd64.gz
mv govc_0.20.0_linux_amd64 /usr/local/bin/govc
chmod +x /usr/local/bin/govc
```

Configure the CLI with the vSphere settings
```
export GOVC_URL='vcenter.example.com'
export GOVC_USERNAME='VSPHERE_ADMIN_USER'
export GOVC_PASSWORD='VSPHERE_ADMIN_PASSWORD'
export GOVC_NETWORK='VM Network'
export GOVC_DATASTORE='Datastore'
export GOVC_INSECURE=1 # If the host above uses a self-signed cert
```

Test the govc CLI settings
```
govc ls
govc about
```

If you don't have a Folder already then you have to create one
(The folder must have the same name as the OCP4 cluster)
```
govc folder.create /Datacenter/vm/Production/ocp4
```

If you don't have a Resource Pool already then you have to create one
```
govc pool.create /Datacenter/host/Cluster/Resources/openshift
```

To see the available Resource Pools
```
govc find / -type p
```

Download the OVA and import it into the Template Repository
```
curl -O https://mirror.openshift.com/pub/openshift-v4/dependencies/rhcos/4.3/4.3.8/rhcos-4.3.8-x86_64-vmware.x86_64.ova
```

Verify that the Template options are the ones you want
```
govc import.spec rhcos-4.3.8-x86_64-vmware.x86_64.ova | python -m json.tool > rhcos.json
vi rhcos.json
```

Import the template and mark it as such
```
govc import.ova -name=rhcos-4.3.8 -pool=/Datacenter/host/Cluster/Resources -ds=Datastore -folder=templates -options=rhcos.json ./rhcos-4.3.8-x86_64-vmware.x86_64.ova
govc vm.markastemplate /Datacenter/vm/templates/rhcos-4.3.8
```

# Build the Cluster
Download the OpenShift client
```
OCP_VERSION=4.4.17
curl -O https://mirror.openshift.com/pub/openshift-v4/clients/ocp/${OCP_VERSION}/openshift-install-linux-${OCP_VERSION}.tar.gz
curl -O https://mirror.openshift.com/pub/openshift-v4/clients/ocp/${OCP_VERSION}/openshift-client-linux-${OCP_VERSION}.tar.gz
tar xzvf openshift-install-linux-${OCP_VERSION}.tar.gz
tar xzvf openshift-client-linux-${OCP_VERSION}.tar.gz
cp openshift-install /usr/local/bin
cp oc /usr/local/bin
```

Export a variable with the cluster ID
```
export CLUSTER_ID=ocp4
```

Create a folder for the cluster configuration files
```
mkdir $CLUSTER_ID
```

Create an install-config.yaml
```
cat << EOF > $CLUSTER_ID/install-config.yaml
---
apiVersion: v1
baseDomain: example.com
proxy:
  httpProxy: http://192.168.0.101:8080
  httpsProxy: http://192.168.0.101:8080
compute:
- hyperthreading: Enabled
  name: worker
  replicas: 0 
controlPlane:
  hyperthreading: Enabled
  name: master
  replicas: 3
metadata:
  name: closprod
platform:
  vsphere:
    vcenter: vcentercc.example.com
    username: VSPHERE_DYNAMIC_PROVISIONING_USER
    password: VSPHERE_DYNAMIC_PROVISIONING_PASSWORD
    datacenter: Cluster
    defaultDatastore: Datastore
networking:
  clusterNetworks:
  - cidr: "10.128.0.0/14"
    hostPrefix: 23
  machineCIDR: "192.168.0.0/24"
  serviceCIDR: "172.30.0.0/16"
fips: false 
pullSecret: '{"auths": ...}'
sshKey: 'ssh-rsa AAAA...' 
EOF
```

Generate the Kubernetes manifests for the cluster
```
openshift-install create manifests --dir=$CLUSTER_ID
```

Set the flag mastersSchedulable to false
```
sed -i 's/mastersSchedulable: true/mastersSchedulable: false/g' $CLUSTER_ID/manifests/cluster-scheduler-02-config.yml
```

Create the ignition config files
```
openshift-install create ignition-configs --dir=$CLUSTER_ID
```

Create a folder for the ignition files in your HTTP server root directory:
```
mkdir -p /var/www/html/$CLUSTER_ID/ignition
```

Copy the ignition config files to the HTTP server root directory:
```
cp $CLUSTER_ID/*.ign /var/www/html/$CLUSTER_ID/ignition
```

Check access to the ignition files through HTTP
```
curl -vk http://bastion.example.com/$CLUSTER_ID/ignition/bootstrap.ign
curl -vk http://bastion.example.com/$CLUSTER_ID/ignition/master.ign
curl -vk http://bastion.example.com/$CLUSTER_ID/ignition/worker.ign
```

Clone the OpenShift installer repo
```
git clone https://github.com/gojeaqui/installer.git
```

Change into the terraform scripts folder
```
cd installer/upi/vsphere/
```

Fill out a terraform.tfvars file with the vCenter, Networking and CPU / Memory configuration.
There is an example terraform.tfvars file in this directory named terraform.tfvars.example.
Read carefully this file to see how to complete the tfvars 
```
cp terraform.tfvars.example terraform.tfvars
vi terraform.tfvars
```

Run `terraform init` to initialize terraform, it will download the required plugins and verify the scripts syntax

Run `terraform plan` to see the changes that terraform is going to apply to the vCenter

Run `terraform apply`.
Terraform will create a folder in the vCenter with the name of the cluster and place the VMs inside that folder.
It will also create a resource group with the same name.

Run `./config-gen.py dhcp terraform.tfvars`.
This script will generate a dhcpd.conf configuration and copy it to the /etc/dhcpd directory, just follow the script instructions.
The script will test the DNS entries to see if they are correctly configured

Run `openshift-install --dir=$CLUSTER_ID wait-for bootstrap-complete`. 
Wait for the bootstrapping to complete.

Run `terraform apply -var 'bootstrap_complete=true'`.
This will destroy the bootstrap VM.

Run `openshift-install --dir=$CLUSTER_ID wait-for install-complete`. 
Wait for the cluster install to finish.

Enjoy your new OpenShift cluster.

If you need to erase the cluster, run `terraform destroy -auto-approve`.
The *terraform destroy* command uses the terraform metadata generated when you run the *terraform init* and *terraform apply* commands, so terraform knows what has been created and safely deletes that (like an undo).
So it is advisable to avoid deleting the terraform.tfstate file and the hidden directory created.
