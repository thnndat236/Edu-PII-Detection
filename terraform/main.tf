// Google Kubernetes Engine
resource "google_container_cluster" "pii-cluster" {
  name     = "${var.project_id}-gke"
  location = var.region

  // We are disabling Autopilot for this cluster,
  // using GKE Standard cluster to have full control,
  // which is necessary for running privileged containers for Elasticsearch.
  enable_autopilot = false

  // This is for the default node pool.
  // For more complex setups such as 'Separately Managed Node Pool'
  // you would define seperate `google_container_node_pool` resources.
  // https://github.com/hashicorp-education/learn-terraform-provision-gke-cluster/blob/main/gke.tf
  initial_node_count = var.cluster_node_count

  // In Standard cluster, we must define the node configuration.
  node_config {
    machine_type = var.machine_type
    disk_size_gb = 100
    disk_type    = "pd-standard"
  }
}

// Jenkins
resource "google_compute_instance" "pii-jenkins" {
  name         = "${var.project_id}-jenkins"
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50
    }
  }

  network_interface {
    network = "default"
    access_config {
      // Ephemeral IP
    }
  }

  metadata = {
    ssh-key        = var.ssh_key,
    startup-script = file("../scripts/jenkins-startup.sh")
  }

  tags = ["jenkins"]
}

resource "google_compute_firewall" "jenkins-firewall" {
  name        = "${var.project_id}-firewall"
  network     = "default"
  description = "Create Firewall allow rules for accessing Jenkins"

  allow {
    protocol = "tcp"
    ports = [
      22,   // SSH
      80,   // HTTP
      443,  // HTTPS
      8080, // Jenkins web interface and GitHub webhoohs
      50000 // Jenkins agents
    ]
  }

  source_ranges = ["0.0.0.0/0"] // allow all traffic
  target_tags   = ["jenkins"]
}
