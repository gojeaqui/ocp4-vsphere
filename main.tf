provider "vsphere" {
  user                 = "${var.vsphere_user}"
  password             = "${var.vsphere_password}"
  vsphere_server       = "${var.vsphere_server}"
  allow_unverified_ssl = true
}

data "vsphere_datacenter" "dc" {
  name = "${var.vsphere_datacenter}"
}

module "bootstrap" {
  source = "./machine"

  host_names       = ["${var.bootstrap_name}"]
  instance_count   = "${var.bootstrap_complete ? 0 : 1}"
  ignition_url     = "${var.ignition_url}/bootstrap.ign"
  resource_pool    = "${var.vm_resource_pool}"
  datastore        = "${var.vsphere_datastore}"
  folder           = "${var.vm_folder}"
  network          = "${var.vm_network}"
  datacenter_id    = "${data.vsphere_datacenter.dc.id}"
  template         = "${var.vm_template}"
  cluster_domain   = "${var.cluster_domain}"
  ipam             = "${var.ipam}"
  ipam_token       = "${var.ipam_token}"
  ip_addresses     = ["${var.bootstrap_ip}"]
  machine_cidr     = "${var.machine_cidr}"
  gateway_ip       = "${var.gateway_ip}"
  dns_ips          = ["${var.dns_ips}"]
  memory           = ["${var.bootstrap_memory}"]
  num_cpu          = ["${var.bootstrap_cpus}"]
}

module "control_plane" {
  source = "./machine"

  host_names       = ["${var.control_plane_names}"]
  instance_count   = "${var.control_plane_count}"
  ignition_url     = "${var.ignition_url}/master.ign"
  resource_pool    = "${var.vm_resource_pool}"
  folder           = "${var.vm_folder}"
  datastore        = "${var.vsphere_datastore}"
  network          = "${var.vm_network}"
  datacenter_id    = "${data.vsphere_datacenter.dc.id}"
  template         = "${var.vm_template}"
  cluster_domain   = "${var.cluster_domain}"
  ipam             = "${var.ipam}"
  ipam_token       = "${var.ipam_token}"
  ip_addresses     = ["${var.control_plane_ips}"]
  machine_cidr     = "${var.machine_cidr}"
  gateway_ip       = "${var.gateway_ip}"
  dns_ips          = ["${var.dns_ips}"]
  memory           = ["${var.control_plane_memory}"]
  num_cpu          = ["${var.control_plane_cpus}"]
}

module "compute" {
  source = "./machine"

  host_names       = ["${var.compute_names}"]
  instance_count   = "${var.compute_count}"
  ignition_url     = "${var.ignition_url}/worker.ign"
  resource_pool    = "${var.vm_resource_pool}"
  folder           = "${var.vm_folder}"
  datastore        = "${var.vsphere_datastore}"
  network          = "${var.vm_network}"
  datacenter_id    = "${data.vsphere_datacenter.dc.id}"
  template         = "${var.vm_template}"
  cluster_domain   = "${var.cluster_domain}"
  ipam             = "${var.ipam}"
  ipam_token       = "${var.ipam_token}"
  ip_addresses     = ["${var.compute_ips}"]
  machine_cidr     = "${var.machine_cidr}"
  gateway_ip       = "${var.gateway_ip}"
  dns_ips          = ["${var.dns_ips}"]
  memory           = ["${var.compute_memory}"]
  num_cpu          = ["${var.compute_cpus}"]
}

