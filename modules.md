h2. terraform-clover-gke_network_roles
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-clover-gke_network_roles
h4. SSH: 
git@github.corp.clover.com:clover/terraform-clover-gke_network_roles.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/gke_network_roles/clover/1.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_project_iam_member
{code}


h2. terraform-clover-mdb-provision
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-clover-mdb-provision
h4. SSH: 
git@github.corp.clover.com:clover/terraform-clover-mdb-provision.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover/0.3.8


h2. terraform-clover-mdb-query
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-clover-mdb-query
h4. SSH: 
git@github.corp.clover.com:clover/terraform-clover-mdb-query.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-query/clover/0.2.3
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-artifactory-test
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-artifactory-test
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-artifactory-test.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/artifactory-test/google/1.0.3
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_disk
google_compute_attached_disk
random_pet
google_sql_database_instance
google_sql_user
{code}


h2. terraform-google-budget
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-budget
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-budget.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/budget/google/0.0.6
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_billing_budget
google_project_service
{code}


h2. terraform-google-cdn-bucket
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-cdn-bucket
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-cdn-bucket.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/cdn-bucket/google/2.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_service_account
google_storage_bucket
google_storage_bucket_iam_member
google_compute_managed_ssl_certificate
google_compute_global_address
google_compute_backend_bucket
google_compute_url_map
google_compute_global_forwarding_rule
google_compute_ssl_policy
google_compute_target_https_proxy
{code}


h2. terraform-google-cloud_native_resource_management
h4. Description: 
Config Connector for managing google resources via kubernetes manifest files
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-cloud_native_resource_management
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-cloud_native_resource_management.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/cloud_native_resource_management/google/0.0.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_service_account
google_project_iam_member
google_service_account_key
kubernetes_namespace
kubernetes_secret
{code}


h2. terraform-google-cloudmysql
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-cloudmysql
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-cloudmysql.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/cloudmysql/google/1.0.3
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_sql_database_instance
{code}


h2. terraform-google-cloudsql
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-cloudsql
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-cloudsql.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/cloudsql/google/6.0.7
h4. Embedded Resources
{code:theme=Midnight|language=bash}
random_pet
google_sql_database_instance
google_sql_user
google_sql_database
{code}


h2. terraform-google-container_registry
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-container_registry
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-container_registry.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/container_registry/google/0.0.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_service_account
{code}


h2. terraform-google-database_ha
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-database_ha
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-database_ha.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/database_ha/google/2.1.1
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/singleinstance/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-datacenter_auth
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_auth
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_auth.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_auth/google/5.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/cloudsql/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-datacenter_cos
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_cos
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_cos.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_cos/google/10.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-datacenter_edge
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_edge
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_edge.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_edge/google/7.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-datacenter_infra
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_infra
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_infra.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_infra/google/6.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/internal-tcp-lb/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_health_check
{code}


h2. terraform-google-datacenter_network
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_network
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_network.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_network/google/1.0.2
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_vpn_tunnel
google_compute_route
google_compute_vpn_gateway
google_compute_address
google_dns_record_set
google_compute_forwarding_rule
google_compute_subnetwork
google_dns_managed_zone
{code}


h2. terraform-google-datacenter_pay
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_pay
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_pay.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_pay/google/8.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/cloudsql/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-datacenter_rivus
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_rivus
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_rivus.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_rivus/google/2.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_storage_bucket
google_kms_key_ring
{code}


h2. terraform-google-datacenter_tokenization
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-datacenter_tokenization
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-datacenter_tokenization.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/datacenter_tokenization/google/8.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]


h2. terraform-google-elastic
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-elastic
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-elastic.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/elastic/google/0.4.1
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-forseti
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-forseti
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-forseti.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/forseti/google/1.0.4
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/singleinstance/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/cloudsql/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
random_id
random_integer
null_resource
google_project_service
tls_private_key
kubernetes_namespace
google_service_account_iam_binding
helm_release
google_dns_record_set
google_service_account
google_project_iam_member
google_storage_bucket_object
google_storage_bucket
{code}


h2. terraform-google-function-external-lb
h4. Description: 
Terraform Module Repository for the managing a generic external load balancer that sends traffic to a GCP function
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-function-external-lb
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-function-external-lb.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/function-external-lb/google/0.2.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_region_network_endpoint_group
google_compute_security_policy
google_compute_ssl_certificate
google_compute_global_forwarding_rule
google_compute_target_https_proxy
google_compute_url_map
google_compute_backend_service
google_compute_target_http_proxy
google_compute_global_address
google_dns_record_set
{code}


h2. terraform-google-hostlist
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-hostlist
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-hostlist.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/hostlist/google/0.2.5


h2. terraform-google-interconnect-attachment
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-interconnect-attachment
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-interconnect-attachment.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/interconnect-attachment/google/1.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_router
google_compute_interconnect_attachment
google_compute_router_interface
google_compute_router_peer
{code}


h2. terraform-google-internal-tcp-lb
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-internal-tcp-lb
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-internal-tcp-lb.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/internal-tcp-lb/google/4.1.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_address
google_dns_record_set
google_compute_forwarding_rule
google_compute_region_backend_service
{code}


h2. terraform-google-jenkins-test
h4. Description: 
Module for jenkins test instance
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-jenkins-test
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-jenkins-test.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/jenkins-test/google/1.0.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]


h2. terraform-google-kubernetes_alerts
h4. Description: 
Repo to manage admin, CI, dev and prod kubernetes clusters and their resources.
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-kubernetes_alerts
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-kubernetes_alerts.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/kubernetes_alerts/google/2.3.3
h4. Embedded Resources
{code:theme=Midnight|language=bash}
wavefront_alert_target
wavefront_alert
{code}


h2. terraform-google-kubernetes_cluster
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-kubernetes_cluster
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-kubernetes_cluster.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/kubernetes_cluster/google/7.1.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_container_cluster
google_container_node_pool
google_service_account
google_project_iam_member
{code}


h2. terraform-google-kubernetes_operational_charts
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-kubernetes_operational_charts
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-kubernetes_operational_charts.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/kubernetes_operational_charts/google/3.3.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
helm_release
kubernetes_service_account
kubernetes_cluster_role_binding
{code}


h2. terraform-google-kubernetes_proxy
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-kubernetes_proxy
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-kubernetes_proxy.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/kubernetes_proxy/google/1.3.6
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/internal-tcp-lb/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_health_check
{code}


h2. terraform-google-lb_http
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-lb_http
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-lb_http.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/lb_http/google/5.3.7
h4. Embedded Resources
{code:theme=Midnight|language=bash}
random_string
google_compute_ssl_certificate
google_compute_managed_ssl_certificate
google_compute_ssl_policy
google_compute_global_address
google_compute_global_forwarding_rule
google_compute_target_https_proxy
google_compute_url_map
google_compute_backend_service
google_compute_health_check
{code}


h2. terraform-google-project
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-project
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-project.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/project/google/6.0.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_router
google_compute_router_nat
google_compute_shared_vpc_service_project
google_compute_network
google_compute_subnetwork
google_compute_global_address
google_service_networking_connection
google_compute_network_peering
google_compute_vpn_gateway
google_compute_address
google_dns_record_set
google_compute_forwarding_rule
google_compute_vpn_tunnel
google_compute_route
google_compute_firewall
google_dns_managed_zone
{code}


h2. terraform-google-proxy_egress
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-proxy_egress
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-proxy_egress.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/proxy_egress/google/1.2.1
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/internal-tcp-lb/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service_nat/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_health_check
{code}


h2. terraform-google-router
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-router
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-router.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/router/google/1.0.4
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-service
h4. Description: 
This module is pending deprecation and terraform-google-service-ha should be used instead.
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service/google/7.0.6
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_address
google_compute_instance
google_dns_record_set
google_compute_instance_group
google_compute_disk
google_compute_attached_disk
{code}


h2. terraform-google-service-bootdisk
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service-bootdisk
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service-bootdisk.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service-bootdisk/google/0.0.2
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_address
google_compute_instance
google_compute_disk
google_dns_record_set
google_compute_instance_group
google_compute_attached_disk
{code}


h2. terraform-google-service-ha
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service-ha
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service-ha.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google/8.2.3
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_address
google_dns_record_set
google_compute_instance_group
google_compute_instance
google_compute_disk
google_compute_region_disk
google_compute_attached_disk
{code}


h2. terraform-google-service_datadisk
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service_datadisk
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service_datadisk.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service_datadisk/google/2.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-service_datadisk_nat
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service_datadisk_nat
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service_datadisk_nat.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service_datadisk_nat/google/1.0.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
null_resource
{code}


h2. terraform-google-service_nat
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-service_nat
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-service_nat.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/service_nat/google/4.0.1
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_address
google_compute_instance
google_dns_record_set
google_compute_instance_group
google_compute_disk
google_compute_attached_disk
{code}


h2. terraform-google-shared-vpc
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-shared-vpc
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-shared-vpc.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/shared-vpc/google/2.1.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_project
google_project_service
google_compute_shared_vpc_host_project
google_compute_router
google_compute_router_nat
google_compute_network
google_compute_subnetwork
google_project_iam_member
google_compute_global_address
google_service_networking_connection
google_compute_network_peering
google_compute_vpn_gateway
google_compute_address
google_dns_record_set
google_compute_forwarding_rule
google_compute_vpn_tunnel
google_compute_route
google_compute_firewall
{code}


h2. terraform-google-singleinstance
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-singleinstance
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-singleinstance.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/singleinstance/google/5.0.2
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/mdb-provision/clover]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_region_disk
google_compute_attached_disk
google_compute_disk
google_compute_address
google_compute_instance
google_dns_record_set
{code}


h2. terraform-google-slb_external
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-slb_external
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-slb_external.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/slb_external/google/2.2.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/tcp-proxy-lb/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/vip/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_global_address
google_compute_address
google_compute_http_health_check
google_compute_health_check
{code}


h2. terraform-google-spinnaker
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-spinnaker
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-spinnaker.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/spinnaker/google/0.1.5
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/singleinstance/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_service_account
google_project_iam_member
google_service_account_iam_member
google_storage_bucket
google_storage_bucket_iam_member
google_compute_address
google_dns_record_set
google_redis_instance
{code}


h2. terraform-google-tcp-proxy-lb
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-tcp-proxy-lb
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-tcp-proxy-lb.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/tcp-proxy-lb/google/2.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_global_address
google_dns_record_set
google_compute_global_forwarding_rule
google_compute_target_tcp_proxy
google_compute_backend_service
google_compute_health_check
google_compute_target_http_proxy
google_compute_url_map
{code}


h2. terraform-google-vault
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-vault
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-vault.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/vault/google/4.1.0
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/service-ha/google]
[https://terraform.corp.clover.com/app/clover/modules/show/clover/internal-tcp-lb/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_health_check
google_kms_key_ring
google_kms_crypto_key
google_kms_crypto_key_iam_binding
google_service_account
google_storage_bucket
google_storage_bucket_iam_binding
google_compute_disk
google_compute_attached_disk
google_compute_resource_policy
{code}


h2. terraform-google-vip
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-vip
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-vip.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/vip/google/2.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_dns_record_set
google_compute_forwarding_rule
google_compute_target_pool
{code}


h2. terraform-google-vip_regional
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-vip_regional
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-vip_regional.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/vip_regional/google/0.3.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_dns_record_set
google_compute_region_backend_service
google_compute_forwarding_rule
{code}


h2. terraform-google-vpn
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-google-vpn
h4. SSH: 
git@github.corp.clover.com:clover/terraform-google-vpn.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/vpn/google/2.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
google_compute_vpn_tunnel
google_compute_router_interface
google_compute_router_peer
{code}


h2. terraform-kubernetes-privoxy
h4. Description: 
Create proxy using privoxy to connect to private kubernetes cluster
h4. URL: 
https://github.corp.clover.com/clover/terraform-kubernetes-privoxy
h4. SSH: 
git@github.corp.clover.com:clover/terraform-kubernetes-privoxy.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/privoxy/kubernetes/0.0.1
h4. Embedded Resources
{code:theme=Midnight|language=bash}
kubernetes_deployment
kubernetes_service
google_dns_record_set
{code}


h2. terraform-puppet-tester
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-puppet-tester
h4. SSH: 
git@github.corp.clover.com:clover/terraform-puppet-tester.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/tester/puppet/0.0.1
h4. Embedded Modules
[https://terraform.corp.clover.com/app/clover/modules/show/clover/singleinstance/google]
h4. Embedded Resources
{code:theme=Midnight|language=bash}
random_string
random_password
null_resource
{code}


h2. terraform-vault-approle
h4. Description: 
None
h4. URL: 
https://github.corp.clover.com/clover/terraform-vault-approle
h4. SSH: 
git@github.corp.clover.com:clover/terraform-vault-approle.git
h4. Terraform Enterprise: 
https://terraform.corp.clover.com/app/clover/modules/show/clover/approle/vault/1.0.0
h4. Embedded Resources
{code:theme=Midnight|language=bash}
vault_approle_auth_backend_role_secret_id
{code}


