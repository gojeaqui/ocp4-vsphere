//////
// vSphere variables
//////

variable "vsphere_server" {
  type        = "string"
  description = "This is the vSphere server for the environment."
}

variable "vsphere_user" {
  type        = "string"
  description = "vSphere server user for the environment."
}

variable "vsphere_password" {
  type        = "string"
  description = "vSphere server password"
}

variable "vsphere_cluster" {
  type        = "string"
  description = "This is the name of the vSphere cluster."
}

variable "vsphere_datacenter" {
  type        = "string"
  description = "This is the name of the vSphere data center."
}

variable "vsphere_datastore" {
  type        = "string"
  description = "This is the name of the vSphere data store."
}

variable "vm_template" {
  type        = "string"
  description = "This is the name of the VM template to clone."
}

variable "vm_network" {
  type        = "string"
  description = "This is the name of the publicly accessible network for cluster ingress and access."
}

variable "vm_folder" {
  type        = "string"
  description = "Name of the folder where the OCP cluster VMs will be created"
}

variable "vm_resource_pool" {
  type        = "string"
  description = "Name of the Resource Pool where the OCP cluster VMs will be assigned"
}

variable "ipam" {
  type        = "string"
  description = "The IPAM server to use for IP management."
  default     = ""
}

variable "ipam_token" {
  type        = "string"
  description = "The IPAM token to use for requests."
  default     = ""
}

/////////
// OpenShift cluster variables
/////////

variable "cluster_id" {
  type        = "string"
  description = "This cluster id must be of max length 27 and must have only alphanumeric or hyphen characters."
}

variable "base_domain" {
  type        = "string"
  description = "The base DNS zone to add the sub zone to."
}

variable "cluster_domain" {
  type        = "string"
  description = "The base DNS zone to add the sub zone to."
}

variable "machine_cidr" {
  type = "string"
}

variable "gateway_ip" {
  type = "string"
}

variable "dns_ips" {
  type    = "list"
}

variable "ignition_url" {
  type = "string"
}

/////////
// Bootstrap machine variables
/////////

variable "bootstrap_complete" {
  type    = "string"
  default = "false"
}

variable "bootstrap_ip" {
  type    = "list"
}

variable "bootstrap_name" {
  type    = "list"
}

variable "bootstrap_memory" {
  type    = "list"
}

variable "bootstrap_cpus" {
  type    = "list"
}

///////////
// Control Plane machine variables
///////////

variable "control_plane_count" {
  type    = "string"
  default = "3"
}

variable "control_plane_ips" {
  type    = "list"
}

variable "control_plane_names" {
  type    = "list"
}


variable "control_plane_memory" {
  type    = "list"
}

variable "control_plane_cpus" {
  type    = "list"
}

//////////
// Compute machine variables
//////////

variable "compute_count" {
  type    = "string"
  default = "3"
}

variable "compute_ips" {
  type    = "list"
}

variable "compute_names" {
  type    = "list"
}

variable "compute_memory" {
  type    = "list"
}

variable "compute_cpus" {
  type    = "list"
}

