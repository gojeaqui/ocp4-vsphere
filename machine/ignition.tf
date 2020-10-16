provider "ignition" {
  version = "1.1.0"
}

locals {
  mask = "${element(split("/", var.machine_cidr), 1)}"

  ignition_encoded = "data:text/plain;charset=utf-8;base64,${base64encode(var.ignition)}"
}

data "ignition_file" "hostname" {
  count = "${var.instance_count}"

  filesystem = "root"
  path       = "/etc/hostname"
  mode       = "420"

  content {
    content = "${var.host_names[count.index]}.${var.cluster_domain}"
  }
}

data "ignition_file" "static_ip" {
  count = "${var.instance_count}"

  filesystem = "root"
  path       = "/etc/sysconfig/network-scripts/ifcfg-ens192"
  mode       = "420"

  content {
    content = <<EOF
TYPE=Ethernet
BOOTPROTO=none
NAME=ens192
DEVICE=ens192
ONBOOT=yes
IPADDR=${local.ip_addresses[count.index]}
PREFIX=${local.mask}
GATEWAY=${var.gateway_ip}
DOMAIN=${var.cluster_domain}
DNS1=${var.dns_ips[0]}
DNS2=${var.dns_ips[1]}
DNS3=${var.dns_ips[2]}
EOF
  }
}

data "ignition_systemd_unit" "restart" {
  count = "${var.instance_count}"

  name = "restart.service"

  content = <<EOF
[Unit]
ConditionFirstBoot=yes
[Service]
Type=idle
ExecStart=/sbin/reboot
[Install]
WantedBy=multi-user.target
EOF
}

data "ignition_config" "ign" {
  count = "${var.instance_count}"

  append {
    source = "${var.ignition_url}" 
    //source = "${var.ignition_url != "" ? var.ignition_url : local.ignition_encoded}"
  }

  systemd = [
    "${data.ignition_systemd_unit.restart.*.id[count.index]}",
  ]

  files = [
    "${data.ignition_file.hostname.*.id[count.index]}",
    "${data.ignition_file.static_ip.*.id[count.index]}",
  ]
}

