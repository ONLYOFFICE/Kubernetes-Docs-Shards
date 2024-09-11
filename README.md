# Kubernetes-Docs-Shards
ONLYOFFICE Docs for Kubernetes

## Contents
- [Introduction](#introduction)
- [Deploy prerequisites](#deploy-prerequisites)
  * [1. Add Helm repositories](#1-add-helm-repositories)
  * [2. Install Persistent Storage](#2-install-persistent-storage)
  * [3. Deploy Redis](#3-deploy-redis)
  * [4. Configure dependent charts](#4-configure-dependent-charts)
    + [4.1 Configure ingress-nginx/kubernetes subchart](#41-configure-ingress-nginxkubernetes-subchart)
  * [5. Deploy StatsD exporter](#5-deploy-statsd-exporter)
    + [5.1 Add Helm repositories](#51-add-helm-repositories)
    + [5.2 Installing Prometheus](#52-installing-prometheus)
    + [5.3 Installing StatsD exporter](#53-installing-statsd-exporter)
  * [6. Make changes to Node-config configuration files](#6-make-changes-to-Node-config-configuration-files)
    + [6.1 Create a ConfigMap containing a json file](#61-create-a-configmap-containing-a-json-file)
    + [6.2 Specify parameters when installing ONLYOFFICE Docs](#62-specify-parameters-when-installing-onlyoffice-docs)
  * [7. Add custom Fonts](#7-add-custom-fonts)
  * [8. Add Plugins](#8-add-plugins)
  * [9. Change interface themes](#9-change-interface-themes)
    + [9.1 Create a ConfigMap containing a json file](#91-create-a-configmap-containing-a-json-file)
    + [9.2 Specify parameters when installing ONLYOFFICE Docs](#92-specify-parameters-when-installing-onlyoffice-docs)
- [Deploy ONLYOFFICE Docs](#deploy-onlyoffice-docs)
  * [1. Deploy the ONLYOFFICE Docs license](#1-deploy-the-onlyoffice-docs-license)
    + [1.1 Create secret](#11-create-secret)
    + [1.2 Specify parameters when installing ONLYOFFICE Docs](#12-specify-parameters-when-installing-onlyoffice-docs)
  * [2. Deploy ONLYOFFICE Docs](#2-deploy-onlyoffice-docs)
  * [3. Uninstall ONLYOFFICE Docs](#3-uninstall-onlyoffice-docs)
  * [4. Parameters](#4-parameters)
  * [5. Configuration and installation details](#5-configuration-and-installation-details)
  * [5.1 Example deployment (optional)](#51-example-deployment-optional)
  * [5.2 Metrics deployment (optional)](#52-metrics-deployment-optional)
  * [5.3 Expose ONLYOFFICE Docs via HTTPS](#53-expose-onlyoffice-docs-via-https)
  * [6. Scale ONLYOFFICE Docs (optional)](#6-scale-onlyoffice-docs-optional) 
      + [6.1 Horizontal Pod Autoscaling](#61-horizontal-pod-autoscaling)
      + [6.2 Manual scaling](#62-manual-scaling)
  * [7. Update ONLYOFFICE Docs](#7-update-onlyoffice-docs) 
  * [8. Update ONLYOFFICE Docs license (optional)](#8-update-onlyoffice-docs-license-optional)
  * [9. ONLYOFFICE Docs installation test (optional)](#9-onlyoffice-docs-installation-test-optional)
  * [10. Access to the info page (optional)](#10-access-to-the-info-page-optional)
  * [11. Deploy ONLYOFFICE Docs with your own dependency (optional)](#11-deploy-onlyoffice-docs-with-your-own-dependency-optional)
  * [11.1 Use your own nginx-ingress controller](#111-use-your-own-nginx-ingress-controller)
- [Using Grafana to visualize metrics (optional)](#using-grafana-to-visualize-metrics-optional)
  * [1. Deploy Grafana](#1-deploy-grafana)
    + [1.1 Deploy Grafana without installing ready-made dashboards](#11-deploy-grafana-without-installing-ready-made-dashboards)
    + [1.2 Deploy Grafana with the installation of ready-made dashboards](#12-deploy-grafana-with-the-installation-of-ready-made-dashboards)
  * [2 Access to Grafana via Ingress](#2-access-to-grafana-via-ingress)
  * [3. View gathered metrics in Grafana](#3-view-gathered-metrics-in-grafana)

## Introduction

- You must have a Kubernetes cluster installed. Please, checkout [the reference](https://kubernetes.io/docs/setup/) to set up Kubernetes.
- You should also have a local configured copy of `kubectl`. See [this](https://kubernetes.io/docs/tasks/tools/install-kubectl/) guide how to install and configure `kubectl`.
- You should install Helm v3.7+. Please follow the instruction [here](https://helm.sh/docs/intro/install/) to install it.

## Deploy prerequisites

### 1. Add Helm repositories

```bash
$ helm repo add bitnami https://charts.bitnami.com/bitnami
$ helm repo add nfs-server-provisioner https://kubernetes-sigs.github.io/nfs-ganesha-server-and-external-provisioner
$ helm repo add onlyoffice https://download.onlyoffice.com/charts/stable
$ helm repo update
```

### 2. Install Persistent Storage

Install NFS Server Provisioner

Note: Pesistent storage will be used for forgotten and error files

Note: When installing NFS Server Provisioner, Storage Classes - `NFS` is created.

```bash
$ helm install nfs-server nfs-server-provisioner/nfs-server-provisioner \
  --set persistence.enabled=true \
  --set persistence.storageClass=PERSISTENT_STORAGE_CLASS \
  --set persistence.size=PERSISTENT_SIZE
```

- `PERSISTENT_STORAGE_CLASS` is a Persistent Storage Class available in your Kubernetes cluster.

  Persistent Storage Classes for different providers:
  - Amazon EKS: `gp2`
  - Digital Ocean: `do-block-storage`
  - IBM Cloud: Default `ibmc-file-bronze`. [More storage classes](https://cloud.ibm.com/docs/containers?topic=containers-file_storage)
  - Yandex Cloud: `yc-network-hdd` or `yc-network-ssd`. [More details](https://cloud.yandex.ru/docs/managed-kubernetes/operations/volumes/manage-storage-class)
  - minikube: `standard`
  - k3s: `local-path`

- `PERSISTENT_SIZE` is the total size of all Persistent Storages for the nfs Persistent Storage Class. You can express the size as a plain integer with one of these suffixes: `T`, `G`, `M`, `Ti`, `Gi`, `Mi`. For example: `9Gi`.

See more details about installing NFS Server Provisioner via Helm [here](https://github.com/kubernetes-sigs/nfs-ganesha-server-and-external-provisioner/tree/master/charts/nfs-server-provisioner).

Configure a Persistent Volume Claim

*The PersistentVolume type to be used for PVC placement must support Access Mode [ReadWriteMany](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes).*
*Also, PersistentVolume must have as the owner the user from whom the ONLYOFFICE Docs will be started. By default it is `ds` (101:101).*

Note: If you want to enable `WOPI`, please set the parameter `wopi.enabled=true`. In this case Persistent Storage must be connected to the cluster nodes with the disabled caching attributes for the mounted directory for the clients. For NFS Server Provisioner it can be achieved by adding `noac` option to the parameter `storageClass.mountOptions`. Please find more information [here](https://github.com/kubernetes-sigs/nfs-ganesha-server-and-external-provisioner/blob/master/charts/nfs-server-provisioner/values.yaml#L83).

### 3. Deploy Redis

To install Redis to your cluster, run the following command:

```bash
$ helm install redis bitnami/redis \
  --set architecture=standalone \
  --set master.persistence.storageClass=PERSISTENT_STORAGE_CLASS \
  --set master.persistence.size=8Gi \
  --set metrics.enabled=false
```

Note: Set the `metrics.enabled=true` to enable exposing Redis metrics to be gathered by Prometheus.

See more details about installing Redis via Helm [here](https://github.com/bitnami/charts/tree/main/bitnami/redis).

### 4. Configure dependent charts 

ONLYOFFICE Docs use ingress-nginx by kubernetes as dependencies chart. Bundle nginx-ingress+Redis is used to implement balancing in sharded mode. You can manage the configuration of dependent chart, or disable it to use your own nginx-ingress controller. 

If you want to manage the configuration of ingress-nginx controller dependent chart, please check section [#4.1](#41-configure-ingress-nginxkubernetes-subchart)

(Optional) Also, you can use your own ingress-nginx controller, for more information please refer to step [#11](#11-deploy-onlyoffice-docs-with-your-own-dependency-optional)

#### 4.1 Configure ingress-nginx/kubernetes subchart

ingress-nginx/kubernetes subchart is **enabled by default**

Docs working in high scalability mode (more than 1 shard) only with enabled ingress-nginx controller by kubernetes.

### Ingress-nginx subchart parameters

Some overridden values ​​for the ingress-nginx/Kubernetes subchart can be found in the table below:

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `ingress-nginx.enabled`                                     | Define that to enable or disable ingress-nginx subchart during deployment                                                                                                      | `true`                                                                                    |
| `ingress-nginx.controller.replicaCount`                     | Number of deployed controller replicas                                                                                                                                         | `2`                                                                                       |
| `ingress-nginx.namespaceOverride`                           | Override the ingress-nginx deployment namespace                                                                                                                                | `default`                                                                                 |
| `ingress-nginx.controller.allowSnippetAnnotations`          | This configuration defines if Ingress Controller should allow users to set their own *-snippet annotations, otherwise this is forbidden / dropped when users add those annotations. Global snippets in ConfigMap are still respected | `true`                              |
| `ingress-nginx.controller.config.http-snippet`              | This configuration define parameters for http nginx configuration for enable caching                                                                                           | `[]`                                                                                      |
| `ingress-nginx.service.annotations`                         | Annotations to be added to the external controller service. See controller.service.internal.annotations for annotations to be added to the internal controller service.        | `{}`                                                                                      |
| `ingress-nginx.controller.extraVolumeMounts`                | Additional volumeMounts to the controller main container. Note: These parameters are used to add configuration to allow custom balancing. For more information please check values.yaml  | `[]`                                                                            |
| `ingress-nginx.controller.extraVolumes`                     | Additional volumes to the controller pod. Note: These parameters are used to add configuration to allow custom balancing. For more information please check values.yaml        | `[]`                                                                                      |

See more details about installing ingress-nginx via Helm [here](https://github.com/kubernetes/ingress-nginx/tree/main/charts/ingress-nginx).

### 5. Deploy StatsD exporter

*This step is optional. You can skip step [#5](#5-deploy-statsd-exporter) entirely if you don't want to run StatsD exporter*

#### 5.1 Add Helm repositories

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo add kube-state-metrics https://kubernetes.github.io/kube-state-metrics
$ helm repo update
```

#### 5.2 Installing Prometheus

To install Prometheus to your cluster, run the following command:

```bash
$ helm install prometheus -f https://raw.githubusercontent.com/ONLYOFFICE/Kubernetes-Docs/master/sources/extraScrapeConfigs.yaml prometheus-community/prometheus \
  --set server.global.scrape_interval=1m
```

To change the scrape interval, specify the `server.global.scrape_interval` parameter.

See more details about installing Prometheus via Helm [here](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus).

#### 5.3 Installing StatsD exporter

To install StatsD exporter to your cluster, run the following command:

```
$ helm install statsd-exporter prometheus-community/prometheus-statsd-exporter \
  --set statsd.udpPort=8125 \
  --set statsd.tcpPort=8126 \
  --set statsd.eventFlushInterval=30000ms
```

See more details about installing Prometheus StatsD exporter via Helm [here](https://github.com/prometheus-community/helm-charts/tree/main/charts/prometheus-statsd-exporter).

To allow the StatsD metrics in ONLYOFFICE Docs, follow step [5.2](#52-metrics-deployment-optional)

### 6. Make changes to Node-config configuration files

*This step is optional. You can skip step [#6](#6-make-changes-to-node-config-configuration-files) entirely if you don't need to make changes to the configuration files*

#### 6.1 Create a ConfigMap containing a json file

In order to create a ConfigMap from a file that contains the `local-production-linux.json` structure, you need to run the following command:

```bash
$ kubectl create configmap custom-local-config \
  --from-file=./local-production-linux.json
```

Note: Any name except `local-config` can be used instead of `custom-local-config`.

#### 6.2 Specify parameters when installing ONLYOFFICE Docs

When installing ONLYOFFICE Docs, specify the `extraConf.configMap=custom-local-config` and `extraConf.filename=local-production-linux.json` parameters

Note: If you need to add a configuration file after the ONLYOFFICE Docs is already installed, you need to execute step [6.1](#61-create-a-configmap-containing-a-json-file) 
and then run the `helm upgrade documentserver onlyoffice/docs-shards --set extraConf.configMap=custom-local-config --set extraConf.filename=local-production-linux.json` command or 
`helm upgrade documentserver -f ./values.yaml onlyoffice/docs-shards` if the parameters are specified in the `values.yaml` file.

### 7. Add custom Fonts

*This step is optional. You can skip step [#7](#7-add-custom-fonts) entirely if you don't need to add your fonts*

In order to add fonts to images, you need to rebuild the images. Refer to the relevant steps in [this](https://github.com/ONLYOFFICE/Docker-Docs#building-onlyoffice-docs) manual.
Then specify your images when installing the ONLYOFFICE Docs.

### 8. Add Plugins

*This step is optional. You can skip step [#8](#8-add-plugins) entirely if you don't need to add plugins*

In order to add plugins to images, you need to rebuild the images. Refer to the relevant steps in [this](https://github.com/ONLYOFFICE/Docker-Docs#building-onlyoffice-docs) manual.
Then specify your images when installing the ONLYOFFICE Docs.

### 9. Change interface themes

*This step is optional. You can skip step [#9](#9-change-interface-themes) entirely if you don't need to change the interface themes*

#### 9.1 Create a ConfigMap containing a json file

To create a ConfigMap with a json file that contains the interface themes, you need to run the following command:

```bash
$ kubectl create configmap custom-themes \
  --from-file=./custom-themes.json
```

Note: Instead of `custom-themes` and `custom-themes.json` you can use any other names.

#### 9.2 Specify parameters when installing ONLYOFFICE Docs

When installing ONLYOFFICE Docs, specify the `extraThemes.configMap=custom-themes` and `extraThemes.filename=custom-themes.json` parameters.

Note: If you need to add interface themes after the ONLYOFFICE Docs is already installed, you need to execute step [6.1](#61-create-a-configmap-containing-a-json-file)
and then run the `helm upgrade documentserver onlyoffice/docs-shards --set extraThemes.configMap=custom-themes --set extraThemes.filename=custom-themes.json` command or
`helm upgrade documentserver -f ./values.yaml onlyoffice/docs-shards` if the parameters are specified in the `values.yaml` file.

## Deploy ONLYOFFICE Docs

### 1. Deploy the ONLYOFFICE Docs license

#### 1.1. Create secret

If you have a valid ONLYOFFICE Docs license, create a secret `license` from the file:

```
$ kubectl create secret generic license --from-file=path/to/license.lic
```

Note: The source license file name should be 'license.lic' because this name would be used as a field in the created secret.

#### 1.2. Specify parameters when installing ONLYOFFICE Docs

When installing ONLYOFFICE Docs, specify the `license.existingSecret=license` parameter.

```
$ helm install documentserver onlyoffice/docs-shards --set license.existingSecret=license
```

Note: If you need to add license after the ONLYOFFICE Docs is already installed, you need to execute step [1.1](#11-create-secret) and then run the `helm upgrade documentserver onlyoffice/docs-shards --set license.existingSecret=license` command or `helm upgrade documentserver -f ./values.yaml onlyoffice/docs-shards` if the parameters are specified in the `values.yaml` file.

### 2. Deploy ONLYOFFICE Docs

To deploy ONLYOFFICE Docs with the release name `documentserver`:

```bash
$ helm install documentserver onlyoffice/docs-shards
```

The command deploys ONLYOFFICE Docs on the Kubernetes cluster in the default configuration. The [Parameters](#4-parameters) section lists the parameters that can be configured during installation. 

### 3. Uninstall ONLYOFFICE Docs

To uninstall/delete the `documentserver` deployment:

```bash
$ helm delete documentserver
```

The `helm delete` command removes all the Kubernetes components associated with the chart and deletes the release.

### 4. Parameters

### Common parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `connections.redisConnectorName`                            | Defines which connector to use to connect to Redis. If you need to connect to Redis Sentinel, set the value `ioredis`                                                          | `redis`                                                                                   |
| `connections.redisHost`                                     | The IP address or the name of the Redis host                                                                                                                                   | `redis-master.default.svc.cluster.local`                                                  |
| `connections.redisPort`                                     | The Redis server port number                                                                                                                                                   | `6379`                                                                                    |
| `connections.redisUser`                                     | The Redis [user](https://redis.io/docs/management/security/acl/) name. The value in this parameter overrides the value set in the `options` object in `local-production-linux.json` if you add custom configuration file | `default`                                                        |
| `connections.redisDBNum`                                    | Number of the redis logical database to be [selected](https://redis.io/commands/select/). The value in this parameter overrides the value set in the `options` object in `local-production-linux.json` if you add custom configuration file | `0`                                           |
| `connections.redisClusterNodes`                             | List of nodes in the Redis cluster. There is no need to specify every node in the cluster, 3 should be enough. You can specify multiple values. It must be specified in the `host:port` format | `[]`                                                                      |
| `connections.redisSentinelGroupName`                        | Name of a group of Redis instances composed of a master and one or more slaves. Used if `connections.redisConnectorName` is set to `ioredis`                                   | `mymaster`                                                                                |
| `connections.redisPassword`                                 | The password set for the Redis account. If set to, it takes priority over the `connections.redisExistingSecret`. The value in this parameter overrides the value set in the `options` object in `local-production-linux.json` if you add custom configuration file| `""`                   |
| `connections.redisSecretKeyName`                            | The name of the key that contains the Redis user password                                                                                                                      | `redis-password`                                                                          |
| `connections.redisExistingSecret`                           | Name of existing secret to use for Redis passwords. Must contain the key specified in `connections.redisSecretKeyName`. The password from this secret overrides password set in the `options` object in `local-production-linux.json` | `redis`                                             |
| `connections.redisNoPass`                                   | Defines whether to use a Redis auth without a password. If the connection to Redis server does not require a password, set the value to `true`                                 | `false`                                                                                   |
| `webProxy.enabled`                                          | Specify whether a Web proxy is used in your network to access the Pods of k8s cluster to the Internet                                                                          | `false`                                                                                   |
| `webProxy.http`                                             | Web Proxy address for `HTTP` traffic                                                                                                                                           | `http://proxy.example.com`                                                                |
| `webProxy.https`                                            | Web Proxy address for `HTTPS` traffic                                                                                                                                          | `https://proxy.example.com`                                                               |
| `webProxy.noProxy`                                          | Patterns for IP addresses or k8s services name or domain names that shouldn’t use the Web Proxy                                                                                | `localhost,127.0.0.1,docservice`                                                          |
| `privateCluster`                                            | Specify whether the k8s cluster is used in a private network without internet access                                                                                           | `false`                                                                                   |
| `namespaceOverride`                                         | The name of the namespace in which ONLYOFFICE Docs will be deployed. If not set, the name will be taken from `.Release.Namespace`                                              | `""`                                                                                      |
| `commonLabels`                                              | Defines labels that will be additionally added to all the deployed resources. You can also use `tpl` as the value for the key                                                  | `{}`                                                                                      |
| `commonAnnotations`                                         | Defines annotations that will be additionally added to all the deployed resources. You can also use `tpl` as the value for the key. Some resources may override the values specified here with their own | `{}`                                                            |
| `serviceAccount.create`                                     | Enable ServiceAccount creation                                                                                                                                                 | `false`                                                                                   |
| `serviceAccount.name`                                       | Name of the ServiceAccount to be used. If not set and `serviceAccount.create` is `true` the name will be taken from `.Release.Name` or `serviceAccount.create` is `false` the name will be "default" | `""`                                                                |
| `serviceAccount.annotations`                                | Map of annotations to add to the ServiceAccount. If set to, it takes priority over the `commonAnnotations`                                                                     | `{}`                                                                                      |
| `serviceAccount.automountServiceAccountToken`               | Enable auto mount of ServiceAccountToken on the serviceAccount created. Used only if `serviceAccount.create` is `true`                                                         | `true`                                                                                    |
| `persistence.dsServiceFiles.existingClaim`                  | Name of an existing PVC to use. If not specified, a PVC named "ds-files" will be created                                                                                       | `""`                                                                                      |
| `persistence.dsServiceFiles.annotations`                    | Defines annotations that will be additionally added to "ds-files" PVC. If set to, it takes priority over the `commonAnnotations`                                               | `{}`                                                                                      |
| `persistence.dsServiceFiles.storageClass`                   | PVC Storage Class for ONLYOFFICE Docs data volume                                                                                                                              | `nfs`                                                                                     |
| `persistence.dsServiceFiles.size`                           | PVC Storage Request for ONLYOFFICE Docs volume                                                                                                                                 | `8Gi`                                                                                     |
| `persistence.dsBalancerCache.existingClaim`                 | Name of an existing PVC for nginx cache to use. If not specified, a PVC named "nginx-ingress-pvc" will be created. If specified, set `ingress-nginx.controller.extraVolumes.persistentVolumeClaim.ClaimName`   | `""`                                                      |
| `persistence.dsBalancerCache.annotations`                   | Defines annotations that will be additionally added to "nginx-ingress-pvc" PVC. If set to, it takes priority over the `commonAnnotations`                                      | `{}`                                                                                      |
| `persistence.dsBalancerCache.storageClass`                  | PVC Storage Class for ONLYOFFICE Docs nginx cache volume                                                                                                                       | `nfs`                                                                                     |
| `persistence.dsBalancerCache.size`                          | PVC Storage Request for ONLYOFFICE Docs nginx cache volume                                                                                                                     | `5Gi`                                                                                     |
| `podSecurityContext.enabled`                                | Enable security context for the pods. If set to true, `podSecurityContext` is enabled for all resources describing the podTemplate.                                            | `false`                                                                                   |
| `podSecurityContext.fsGroup`                                | Defines the Group ID to which the owner and permissions for all files in volumes are changed when mounted in the Pod                                                           | `101`                                                                                     |
| `podAntiAffinity.type`                                      | Types of Pod antiaffinity. Allowed values: `soft` or `hard`                                                                                                                    | `soft`                                                                                    |
| `podAntiAffinity.topologyKey`                               | Node label key to match                                                                                                                                                        | `kubernetes.io/hostname`                                                                  |
| `podAntiAffinity.weight`                                    | Priority when selecting node. It is in the range from 1 to 100                                                                                                                 | `100`                                                                                     |
| `nodeSelector`                                              | Node labels for pods assignment. Each ONLYOFFICE Docs services can override the values specified here with its own                                                      | `{}`                                                                                      |
| `tolerations`                                               | Tolerations for pods assignment. Each ONLYOFFICE Docs services can override the values specified here with its own                                                      | `[]`                                                                                      |
| `imagePullSecrets`                                          | Container image registry secret name                                                                                                                                           | `""`                                                                                      |
| `service.existing`                                          | The name of an existing service for ONLYOFFICE Docs. If not specified, a service named `documentserver` will be created                                                 | `""`                                                                                      |
| `service.annotations`                                       | Map of annotations to add to the ONLYOFFICE Docs service. If set to, it takes priority over the `commonAnnotations`                                                     | `{}`                                                                                      |
| `service.type`                                              | ONLYOFFICE Docs service type                                                                                                                                            | `ClusterIP`                                                                               |
| `service.port`                                              | ONLYOFFICE Docs service port                                                                                                                                            | `8888`                                                                                    |
| `service.sessionAffinity`                                   | [Session Affinity](https://kubernetes.io/docs/reference/networking/virtual-ips/#session-affinity) for ONLYOFFICE Docs service. If not set, `None` will be set as the default value | `""`                                                                           |
| `service.sessionAffinityConfig`                             | [Configuration](https://kubernetes.io/docs/reference/networking/virtual-ips/#session-stickiness-timeout) for ONLYOFFICE Docs service Session Affinity. Used if the `service.sessionAffinity` is set | `{}`                                                          |
| `license.existingSecret`                                    | Name of the existing secret that contains the license. Must contain the key `license.lic`                                                                                      | `""`                                                                                      |
| `license.existingClaim`                                     | Name of the existing PVC in which the license is stored. Must contain the file `license.lic`                                                                                   | `""`                                                                                      |
| `log.level`                                                 | Defines the type and severity of a logged event. Possible values are `ALL`, `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL`, `MARK`, `OFF`                                  | `WARN`                                                                                    |
| `log.type`                                                  | Defines the format of a logged event. Possible values are `pattern`, `json`, `basic`, `coloured`, `messagePassThrough`, `dummy`                                                | `pattern`                                                                                 |
| `log.pattern`                                               | Defines the log [pattern](https://github.com/log4js-node/log4js-node/blob/master/docs/layouts.md#pattern-format) if `log.type=pattern`                                         | `[%d] [%p] %c - %.10000m`                                                                 |
| `wopi.enabled`                                              | Defines if `WOPI` is enabled. If the parameter is enabled, then caching attributes for the mounted directory (`PVC`) should be disabled for the client                         | `false`                                                                                   |
| `metrics.enabled`                                           | Specifies the enabling StatsD for ONLYOFFICE Docs                                                                                                                       | `false`                                                                                   |
| `metrics.host`                                              | Defines StatsD listening host                                                                                                                                                  | `statsd-exporter-prometheus-statsd-exporter`                                              |
| `metrics.port`                                              | Defines StatsD listening port                                                                                                                                                  | `8125`                                                                                    |
| `metrics.prefix`                                            | Defines StatsD metrics prefix for backend services                                                                                                                             | `ds.`                                                                                     |
| `jwt.enabled`                                               | Specifies the enabling the JSON Web Token validation by the ONLYOFFICE Docs. Common for inbox and outbox requests                                                       | `true`                                                                                    |
| `jwt.secret`                                                | Defines the secret key to validate the JSON Web Token in the request to the ONLYOFFICE Docs. Common for inbox and outbox requests                                       | `MYSECRET`                                                                                |
| `jwt.header`                                                | Defines the http header that will be used to send the JSON Web Token. Common for inbox and outbox requests                                                                     | `Authorization`                                                                           |
| `jwt.inBody`                                                | Specifies the enabling the token validation in the request body to the ONLYOFFICE Docs                                                                                  | `false`                                                                                   |
| `jwt.inbox`                                                 | JSON Web Token validation parameters for inbox requests only. If not specified, the values of the parameters of the common `jwt` are used                                      | `{}`                                                                                      |
| `jwt.outbox`                                                | JSON Web Token validation parameters for outbox requests only. If not specified, the values of the parameters of the common `jwt` are used                                     | `{}`                                                                                      |
| `jwt.existingSecret`                                        | The name of an existing secret containing variables for jwt. If not specified, a secret named `jwt` will be created                                                            | `""`                                                                                      |
| `extraConf.configMap`                                       | The name of the ConfigMap containing the json file that override the default values                                                                                            | `""`                                                                                      |
| `extraConf.filename`                                        | The name of the json file that contains custom values. Must be the same as the `key` name in `extraConf.ConfigMap`                                                             | `local-production-linux.json`                                                                              |
| `extraThemes.configMap`                                     | The name of the ConfigMap containing the json file that contains the interface themes                                                                                          | `""`                                                                                      |
| `extraThemes.filename`                                      | The name of the json file that contains custom interface themes. Must be the same as the `key` name in `extraThemes.configMap`                                                 | `custom-themes.json`                                                                      |
| `sqlScripts.branchName`                                     | The name of the repository branch from which sql scripts will be downloaded                                                                                                    | `master`                                                                                  |
| `requestFilteringAgent.allowPrivateIPAddress`               | Defines if it is allowed to connect private IP address or not. `requestFilteringAgent` parameters are used if JWT is disabled: `jwt.enabled=false`                             | `false`                                                                                   |
| `requestFilteringAgent.allowMetaIPAddress`                  | Defines if it is allowed to connect meta address or not                                                                                                                        | `false`                                                                                   |
| `requestFilteringAgent.allowIPAddressList`                  | Defines the list of IP addresses allowed to connect. This values are preferred than `requestFilteringAgent.denyIPAddressList`                                                  | `[]`                                                                                      |
| `requestFilteringAgent.denyIPAddressList`                   | Defines the list of IP addresses allowed to connect                                                                                                                            | `[]`                                                                                      |
| `documentserver.terminationGracePeriodSeconds`              | The time to terminate gracefully during which the Pod will have the Terminating status                                                                                         | `60`                                                                                      |
| `documentserver.keysRedisDBNum`                             | The number of the database for storing the balancing results                                                                                                                   | `1`                                                                                       |
| `documentserver.KeysExpireTime`                             | The time in seconds after which the key will be deleted from the balancing database. by default 172800 mean 48 hours                                                           | `172800`                                                                                  |
| `documentserver.ingressCustomConfigMapsNamespace`           | Define where custom controller configmaps will be deployed                                                                                                                     | `default`                                                                                 |
| `documentserver.annotations`                                | Defines annotations that will be additionally added to Documentserver Deployment                                                                                               | `{}`                                                                                      |
| `documentserver.podAnnotations`                             | Map of annotations to add to the Documentserver deployment pods                                                                                                                | `rollme: "{{ randAlphaNum 5 | quote }}"`                                                  |
| `documentserver.replicas`                                   | Number of Documentserver replicas to deploy. If the `documentserver.autoscaling.enabled` parameter is enabled, it is ignored.                                                  | `3`                                                                                       |
| `documentserver.updateStrategy.type`                        | Documentserver deployment update strategy type                                                                                                                                 | `RollingUpdate`                                                                           |
| `documentserver.updateStrategy.rollingUpdate.maxUnavailable` | Maximum number of Documentserver Pods unavailable during the update process                                                                                                   | `25%`                                                                                     |
| `documentserver.updateStrategy.rollingUpdate.maxSurge`      | Maximum number of Documentserver Pods created over the desired number of Pods                                                                                                  | `25%`                                                                                     |
| `documentserver.customPodAntiAffinity`                      | Prohibiting the scheduling of Documentserver Pods relative to other Pods containing the specified labels on the same node                                                      | `{}`                                                                                      |
| `documentserver.podAffinity`                                | Pod affinity rules for Documentserver Pods scheduling by nodes relative to other Pods                                                                                          | `{}`                                                                                      |
| `documentserver.nodeAffinity`                               | Node affinity rules for Documentserver Pods scheduling by nodes                                                                                                                | `{}`                                                                                      |
| `documentserver.nodeSelector`                               | Node labels for Documentserver Pods assignment                                                                                                                                 | `{}`                                                                                      |
| `documentserver.tolerations`                                | Tolerations for Documentserver Pods assignment                                                                                                                                 | `{}`                                                                                      |
| `documentserver.autoscaling.enabled`                        | Enable Documentserver deployment autoscaling                                                                                                                                   | `false`                                                                                   |
| `documentserver.autoscaling.annotations`                    | Defines annotations that will be additionally added to Documentserver deployment HPA                                                                                           | `{}`                                                                                      |
| `documentserver.autoscaling.minReplicas`                    | Documentserver deployment autoscaling minimum number of replicas                                                                                                               | `2`                                                                                       |
| `documentserver.autoscaling.maxReplicas`                    | Documentserver deployment autoscaling maximum number of replicas                                                                                                               | `4`                                                                                       |
| `documentserver.autoscaling.targetCPU.enabled`              | Enable autoscaling of Documentserver deployment by CPU usage percentage                                                                                                        | `true`                                                                                    |
| `documentserver.autoscaling.targetCPU.utilizationPercentage`| Documentserver deployment autoscaling target CPU percentage                                                                                                                    | `70`                                                                                      |
| `documentserver.autoscaling.targetMemory.enabled`           | Enable autoscaling of Documentserver deployment by memory usage percentage                                                                                                     | `false`                                                                                   |
| `documentserver.autoscaling.targetMemory.utilizationPercentage` | Documentserver deployment autoscaling target memory percentage                                                                                                             | `70`                                                                                      |
| `documentserver.autoscaling.customMetricsType`              | Custom, additional or external autoscaling metrics for the documentserver deployment                                                                                           | `[]`                                                                                      |
| `documentserver.autoscaling.behavior`                       | Configuring Documentserver deployment scaling behavior policies for the `scaleDown` and `scaleUp` fields                                                                       | `{}`                                                                                      |
| `documentserver.initContainers.image.repository`            | Documentserver add-shardkey initContainer image repository                                                                                                                     | `onlyoffice/docs-utils`                                                                   |
| `documentserver.initContainers.image.tag`                   | Documentserver add-shardkey initContainer image tag                                                                                                                            | `8.1.1-2`                                                                                 |
| `documentserver.initContainers.image.pullPolicy`            | Documentserver add-shardkey initContainer image pull policy                                                                                                                    | `IfNotPresent`                                                                            |
| `documentserver.initContainers.containerSecurityContext.enabled`  |  Configure a Security Context for Documentserver add-shardkey initContainer container in Pod                                                                             | `false`                                                                                   |
| `documentserver.initContainers.resources.requests`          | The requested resources for the Documentserver add-shardkey initContainer                                                                                                      | `{}`                                                                                      |
| `documentserver.initContainers.resources.limits`            | The resources limits for the Documentserver add-shardkey initContainer                                                                                                         | `{}`                                                                                      |
| `documentserver.initContainers.custom`                      | Custom Documentserver initContainers parameters                                                                                                                                | `[]`                                                                                      |

### documentserver.docservice parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `documentserver.docservice.image.repository`                | Docservice container image repository*                                                                                                                                         | `onlyoffice/docs-docservice-de`                                                           |
| `documentserver.docservice.image.tag`                       | Docservice container image tag                                                                                                                                                 | `8.1.1-2`                                                                                 |
| `documentserver.docservice.image.pullPolicy`                | Docservice container image pull policy                                                                                                                                         | `IfNotPresent`                                                                            |
| `documentserver.docservice.containerSecurityContext.enabled`| Enable security context for the Docservice container                                                                                                                           | `false`                                                                                   |
| `documentserver.docservice.containerPorts.http`             | Define docservice container port                                                                                                                                               | `8000`                                                                                    |
| `documentserver.docservice.readinessProbe.enabled`          | Enable readinessProbe for Docservice container                                                                                                                                 | `true`                                                                                    |
| `documentserver.docservice.livenessProbe.enabled`           | Enable livenessProbe for Docservice container                                                                                                                                  | `true`                                                                                    |
| `documentserver.docservice.startupProbe.enabled`            | Enable startupProbe for Docservice container                                                                                                                                   | `true`                                                                                    |
| `documentserver.docservice.resources.requests`              | The requested resources for the Docservice container                                                                                                                           | `{}`                                                                                      |
| `documentserver.docservice.resources.limits`                | The resources limits for the Docservice container                                                                                                                              | `{}`                                                                                      |


### documentserver.proxy parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `documentserver.proxy.accessLog`                            | Defines the nginx config [access_log](https://nginx.org/en/docs/http/ngx_http_log_module.html#access_log) format directive                                                     | `main`                                                                                    |
| `documentserver.proxy.gzipProxied`                          | Defines the nginx config [gzip_proxied](https://nginx.org/en/docs/http/ngx_http_gzip_module.html#gzip_proxied) directive                                                       | `off`                                                                                     |
| `documentserver.proxy.clientMaxBodySize`                    | Defines the nginx config [client_max_body_size](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size) directive                                       | `100m`                                                                                    |
| `documentserver.proxy.workerConnections`                    | Defines the nginx config [worker_connections](https://nginx.org/en/docs/ngx_core_module.html#worker_connections) directive                                                     | `4096`                                                                                    |
| `documentserver.proxy.workerProcesses`                      | Defines the nginx config worker_processes directive                                                                                                                            | `1`                                                                                       |
| `documentserver.proxy.secureLinkSecret`                     | Defines secret for the nginx config directive [secure_link_md5](https://nginx.org/en/docs/http/ngx_http_secure_link_module.html#secure_link_md5)                               | `verysecretstring`                                                                        |
| `documentserver.proxy.infoAllowedIP`                        | Defines ip addresses for accessing the info page                                                                                                                               | `[]`                                                                                      |
| `documentserver.proxy.infoAllowedUser`                      | Defines user name for accessing the info page. If not set to, Nginx [Basic Authentication](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html) will not be applied to access the info page. For more details, see [here](#10-access-to-the-info-page-optional) | `""` |
| `documentserver.proxy.infoAllowedPassword`                  | Defines user password for accessing the info page. Used if `proxy.infoAllowedUser` is set                                                                                      | `password`                                                                                |
| `documentserver.proxy.infoAllowedSecretKeyName`             | The name of the key that contains the info auth user password. Used if `proxy.infoAllowedUser` is set                                                                          | `info-auth-password`                                                                      |
| `documentserver.proxy.infoAllowedExistingSecret`            | Name of existing secret to use for info auth password. Used if `proxy.infoAllowedUser` is set. Must contain the key specified in `proxy.infoAllowedSecretKeyName`. If set to, it takes priority over the `proxy.infoAllowedPassword` | `""`                                |
| `documentserver.proxy.welcomePage.enabled`                  | Defines whether the welcome page will be displayed                                                                                                                             | `true`                                                                                    |
| `documentserver.proxy.image.repository`                     | Docservice Proxy container image repository*                                                                                                                                   | `onlyoffice/docs-proxy-de`                                                                |
| `documentserver.proxy.image.tag`                            | Docservice Proxy container image tag                                                                                                                                           | `8.1.1-2`                                                                                 |
| `documentserver.proxy.image.pullPolicy`                     | Docservice Proxy container image pull policy                                                                                                                                   | `IfNotPresent`                                                                            |
| `documentserver.proxy.containerSecurityContext.enabled`     | Enable security context for the Proxy container                                                                                                                                | `false`                                                                                   |
| `documentserver.proxy.containerPorts.http`                  | proxy container port                                                                                                                                                           | `8888`                                                                                    |
| `documentserver.proxy.resources.requests`                   | The requested resources for the Proxy container                                                                                                                                | `{}`                                                                                      |
| `documentserver.proxy.resources.limits`                     | The resources limits for the Proxy container                                                                                                                                   | `{}`                                                                                      |
| `documentserver.proxy.readinessProbe.enabled`               | Enable readinessProbe for  Proxy container                                                                                                                                     | `true`                                                                                    |
| `documentserver.proxy.livenessProbe.enabled`                | Enable livenessProbe for Proxy container                                                                                                                                       | `true`                                                                                    |
| `documentserver.proxy.startupProbe.enabled`                 | Enable startupProbe for Proxy container                                                                                                                                        | `true`                                                                                    |

### documentserver.converter parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `documentserver.converter.count`                            | The mumber of Converter containers in the Documentserver Pod                                                                                                                   | `3`                                                                                       |
| `documentserver.converter.image.repository`                 | Converter container image repository*                                                                                                                                          | `onlyoffice/docs-converter-de`                                                            |
| `documentserver.converter.image.tag`                        | Converter container image tag                                                                                                                                                  | `8.1.1-2`                                                                                 |
| `documentserver.converter.image.pullPolicy`                 | Converter container image pull policy                                                                                                                                          | `IfNotPresent`                                                                            |
| `documentserver.converter.containerSecurityContext.enabled` | Enable security context for the Converter container                                                                                                                            | `false`                                                                                   |
| `documentserver.converter.resources.requests`               | The requested resources for the Converter container                                                                                                                            | `{}`                                                                                      |
| `documentserver.converter.resources.limits`                 | The resources limits for the Converter container                                                                                                                               | `{}`                                                                                      |

### documentserver.postgresql parameters

List of parameters for customizing the database inside the documentserver pod

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `documentserver.postgresql.image.repository`                | Postgresql container image repository                                                                                                                                          | `postgres`                                                                                |
| `documentserver.postgresql.image.tag`                       | Postgresql container image tag                                                                                                                                                 | `16`                                                                                      |
| `documentserver.postgresql.image.pullPolicy`                | Postgresql container image pull policy                                                                                                                                         | `IfNotPresent`                                                                            |
| `documentserver.postgresql.containerSecurityContext.enabled`| Enable security context for the Postgresql container                                                                                                                           | `false`                                                                                   |
| `documentserver.postgresql.containerPorts.tcp`              | Postgresql container port                                                                                                                                                      | `5432`                                                                                    |
| `documentserver.postgresql.resources.requests`              | The requested resources for the Postgresql container                                                                                                                           | `{}`                                                                                      |
| `documentserver.postgresql.resources.limits`                | The resources limits for the Postgresql container                                                                                                                              | `{}`                                                                                      |

### documentserver.rabbitmq parameters

List of parameters for broker inside the documentserver pod

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `documentserver.rabbitmq.image.repository`                  | Rabbitmq container image repository                                                                                                                                            | `rabbitmq`                                                                                |
| `documentserver.rabbitmq.image.tag`                         | Rabbitmq container image tag                                                                                                                                                   | `3.12.10`                                                                                 |
| `documentserver.rabbitmq.image.pullPolicy`                  | Rabbitmq container image pull policy                                                                                                                                           | `ifNotPresent`                                                                            |
| `documentserver.rabbitmq.containerSecurityContext.enabled`  | Enable security context for the Rabbitmq container                                                                                                                             | `false`                                                                                   |
| `documentserver.rabbitmq.containerPorts.amqp`               | Rabbitmq container port                                                                                                                                                        | `5672`                                                                                    |
| `documentserver.rabbitmq.resources.requests`                | The requested resources for the Rabbitmq container                                                                                                                             | `{}`                                                                                      |
| `documentserver.rabbitmq.resources.limits`                  | The resources limits for the Rabbitmq container                                                                                                                                | `{}`                                                                                      |

### Example parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `example.enabled`                                           | Enables the installation of Example                                                                                                                                            | `false`                                                                                   |
| `example.annotations`                                       | Defines annotations that will be additionally added to Example StatefulSet. If set to, it takes priority over the `commonAnnotations`                                          | `{}`                                                                                      |
| `example.podAnnotations`                                    | Map of annotations to add to the example pod                                                                                                                                   | `rollme: "{{ randAlphaNum 5 \| quote }}"`                                                 |
| `example.updateStrategy.type`                               | Example StatefulSet update strategy type                                                                                                                                       | `RollingUpdate`                                                                           |
| `example.customPodAntiAffinity`                             | Prohibiting the scheduling of Example Pod relative to other Pods containing the specified labels on the same node                                                              | `{}`                                                                                      |
| `example.podAffinity`                                       | Defines [Pod affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#inter-pod-affinity-and-anti-affinity) rules for Example Pod scheduling by nodes relative to other Pods | `{}`                                                              |
| `example.nodeAffinity`                                      | Defines [Node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity) rules for Example Pod scheduling by nodes                      | `{}`                                                                                      |
| `example.nodeSelector`                                      | Node labels for Example Pods assignment. If set to, it takes priority over the `nodeSelector`                                                                                  | `{}`                                                                                      |
| `example.tolerations`                                       | Tolerations for Example Pods assignment. If set to, it takes priority over the `tolerations`                                                                                   | `[]`                                                                                      |
| `example.image.repository`                                  | Example container image name                                                                                                                                                   | `onlyoffice/docs-example`                                                                 |
| `example.image.tag`                                         | Example container image tag                                                                                                                                                    | `8.1.1-2`                                                                                 |
| `example.image.pullPolicy`                                  | Example container image pull policy                                                                                                                                            | `IfNotPresent`                                                                            |
| `example.containerSecurityContext.enabled`                  | Enable security context for the Example container                                                                                                                              | `false`                                                                                   |
| `example.dsUrl`                                             | ONLYOFFICE Docs external address. It should be changed only if it is necessary to check the operation of the conversion in Example (e.g. http://\<documentserver-address\>/)   | `/`                                                                                |
| `example.resources.requests`                                | The requested resources for the Example container                                                                                                                              | `{}`                                                                                      |
| `example.resources.limits`                                  | The resources limits for the Example container                                                                                                                                 | `{}`                                                                                      |
| `example.extraConf.configMap`                               | The name of the ConfigMap containing the json file that override the default values. See an example of creation [here](https://github.com/ONLYOFFICE/Kubernetes-Docs?tab=readme-ov-file#71-create-a-configmap-containing-a-json-file) | `""`                               |
| `example.extraConf.filename`                                | The name of the json file that contains custom values. Must be the same as the `key` name in `example.extraConf.ConfigMap`                                                     | `local.json`                                                                              |

### Ingress parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `ingress.enabled`                                           | Enable the creation of an ingress for the ONLYOFFICE Docs                                                                                                               | `true`                                                                                   |
| `ingress.annotations`                                       | Map of annotations to add to the Ingress. If set to, it takes priority over the `commonAnnotations`                                                                            | `nginx.ingress.kubernetes.io/proxy-body-size: 100m`                                       |
| `ingress.ingressClassName`                                  | Used to reference the IngressClass that should be used to implement this Ingress                                                                                               | `nginx`                                                                                   |
| `ingress.host`                                              | Ingress hostname for the ONLYOFFICE Docs ingress                                                                                                                        | `""`                                                                                      |
| `ingress.ssl.enabled`                                       | Enable ssl for the ONLYOFFICE Docs ingress                                                                                                                              | `false`                                                                                   |
| `ingress.ssl.secret`                                        | Secret name for ssl to mount into the Ingress                                                                                                                                  | `tls`                                                                                     |
| `ingress.path`                                              | Specifies the path where ONLYOFFICE Docs will be available                                                                                                              | `/`                                                                                       |

### Grafana parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `grafana.enabled`                                           | Enable the installation of resources required for the visualization of metrics in Grafana                                                                                      | `false`                                                                                   |
| `grafana.namespace`                                         | The name of the namespace in which RBAC components and Grafana resources will be deployed. If not set, the name will be taken from `namespaceOverride` if set, or .Release.Namespace | `""`                                                                                |
| `grafana.ingress.enabled`                                   | Enable the creation of an ingress for the Grafana. Used if you set `grafana.enabled` to `true` and want to use Nginx Ingress to access Grafana                                 | `false`                                                                                   |
| `grafana.ingress.annotations`                               | Map of annotations to add to Grafana Ingress. If set to, it takes priority over the `commonAnnotations`                                                                        | `nginx.ingress.kubernetes.io/proxy-body-size: 100m`                                       |
| `grafana.dashboard.enabled`                                 | Enable the installation of ready-made Grafana dashboards. Used if you set `grafana.enabled` to `true`                                                                          | `false`                                                                                   |
| `grafanaDashboard.job.annotations`                          | Defines annotations that will be additionally added to Grafana Dashboard Job. If set to, it takes priority over the `commonAnnotations`                                        | `{}`                                                                                      |
| `grafanaDashboard.job.podAnnotations`                       | Map of annotations to add to the Grafana Dashboard Pod                                                                                                                         | `{}`                                                                                      |
| `grafanaDashboard.job.customPodAntiAffinity`                | Prohibiting the scheduling of Grafana Dashboard Job Pod relative to other Pods containing the specified labels on the same node                                                | `{}`                                                                                      |
| `grafanaDashboard.job.podAffinity`                          | Defines [Pod affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#inter-pod-affinity-and-anti-affinity) rules for Grafana Dashboard Job Pod scheduling by nodes relative to other Pods | `{}`                                                |
| `grafanaDashboard.job.nodeAffinity`                         | Defines [Node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity) rules for Grafana Dashboard Job Pod scheduling by nodes        | `{}`                                                                                      |
| `grafanaDashboard.job.nodeSelector`                         | Node labels for Grafana Dashboard Job Pod assignment. If set to, it takes priority over the `nodeSelector`                                                                     | `{}`                                                                                      |
| `grafanaDashboard.job.tolerations`                          | Tolerations for Grafana Dashboard Job Pod assignment. If set to, it takes priority over the `tolerations`                                                                      | `[]`                                                                                      |
| `grafanaDashboard.job.image.repository`                     | Job by Grafana Dashboard ONLYOFFICE Docs image repository                                                                                                               | `onlyoffice/docs-utils`                                                                   |
| `grafanaDashboard.job.image.tag`                            | Job by Grafana Dashboard ONLYOFFICE Docs image tag                                                                                                                      | `8.1.1-2`                                                                                 |
| `grafanaDashboard.job.image.pullPolicy`                     | Job by Grafana Dashboard ONLYOFFICE Docs image pull policy                                                                                                              | `IfNotPresent`                                                                            |
| `grafanaDashboard.job.containerSecurityContext.enabled`     | Enable security context for the Grafana Dashboard container                                                                                                                    | `false`                                                                                   |
| `grafanaDashboard.job.resources.requests`                   | The requested resources for the job Grafana Dashboard container                                                                                                                | `{}`                                                                                      |
| `grafanaDashboard.job.resources.limits`                     | The resources limits for the job Grafana Dashboard container                                                                                                                   | `{}`                                                                                      |

### Testing parameters

| Parameter                                                   | Description                                                                                                                                                                    | Default                                                                                   |
|-------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------|
| `tests.enabled`                                             | Enable the resources creation necessary for ONLYOFFICE Docs launch testing and connected dependencies availability testing. These resources will be used when running the `helm test` command | `true`                                                              |
| `tests.annotations`                                         | Defines annotations that will be additionally added to Test Pod. If set to, it takes priority over the `commonAnnotations`                                                     | `{}`                                                                                      |
| `tests.customPodAntiAffinity`                               | Prohibiting the scheduling of Test Pod relative to other Pods containing the specified labels on the same node                                                                 | `{}`                                                                                      |
| `tests.podAffinity`                                         | Defines [Pod affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#inter-pod-affinity-and-anti-affinity) rules for Test Pod scheduling by nodes relative to other Pods | `{}`                                                                 |
| `tests.nodeAffinity`                                        | Defines [Node affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#node-affinity) rules for Test Pod scheduling by nodes                         | `{}`                                                                                      |
| `tests.nodeSelector`                                        | Node labels for Test Pod assignment. If set to, it takes priority over the `nodeSelector`                                                                                      | `{}`                                                                                      |
| `tests.tolerations`                                         | Tolerations for Test Pod assignment. If set to, it takes priority over the `tolerations`                                                                                       | `[]`                                                                                      |
| `tests.image.repository`                                    | Test container image name                                                                                                                                                      | `onlyoffice/docs-utils`                                                                   |
| `tests.image.tag`                                           | Test container image tag                                                                                                                                                       | `8.1.1-2`                                                                                 |
| `tests.image.pullPolicy`                                    | Test container image pull policy                                                                                                                                               | `IfNotPresent`                                                                            |
| `tests.containerSecurityContext.enabled`                    | Enable security context for the Test container                                                                                                                                 | `false`                                                                                   |
| `tests.resources.requests`                                  | The requested resources for the test container                                                                                                                                 | `{}`                                                                                      |
| `tests.resources.limits`                                    | The resources limits for the test container                                                                                                                                    | `{}`                                                                                      |

* *Note: The prefix `-de` is specified in the value of the image repository, which means solution type. Possible options:
  - Nothing is specified. For the open-source community version
  - `-de`. For commercial Developer Edition
  - `-ee`. For commercial Enterprise Edition

  If you use the community version, there may be problems with co-editing documents.

  The default value of this parameter refers to the ONLYOFFICE Document Server Developer Edition. To learn more about this edition and compare it with other editions, please see the comparison table on [this page](https://github.com/ONLYOFFICE/DocumentServer#onlyoffice-docs-editions).

Specify each parameter using the `--set key=value[,key=value]` argument to helm install. For example,

```bash
$ helm install documentserver onlyoffice/docs-shards --set ingress.enabled=true,ingress.ssl.enabled=true,ingress.host=example.com
```

This command gives expose ONLYOFFICE Docs via HTTPS.

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```bash
$ helm install documentserver -f values.yaml onlyoffice/docs-shards
```

> **Tip**: You can use the default [values.yaml](values.yaml)

### 5. Configuration and installation details

### 5.1 Example deployment (optional)

To deploy the example, set the `example.enabled` parameter to true:

```bash
$ helm install documentserver onlyoffice/docs-shards --set example.enabled=true
```

### 5.2 Metrics deployment (optional)
To deploy metrics, set `metrics.enabled` to true:

```bash
$ helm install documentserver onlyoffice/docs-shards --set metrics.enabled=true
```

If you want to use Grafana to visualize metrics, set `grafana.enabled` to `true`. If you want to use Nginx Ingress to access Grafana, set `grafana.ingress.enabled` to `true`:

```bash
$ helm install documentserver onlyoffice/docs-shards --set grafana.enabled=true --set grafana.ingress.enabled=true
```

### 5.3 Expose ONLYOFFICE Docs via HTTPS

This type of exposure allows you to enable internal TLS termination for ONLYOFFICE Docs.

Create the `tls` secret with an ssl certificate inside.

Put the ssl certificate and the private key into the `tls.crt` and `tls.key` files and then run:

```bash
$ kubectl create secret generic tls \
  --from-file=./tls.crt \
  --from-file=./tls.key
```

```bash
$ helm install documentserver onlyoffice/docs-shards --set ingress.enabled=true,ingress.ssl.enabled=true,ingress.host=example.com

```

Run the following command to get the `documentserver` ingress IP:

```bash
$ kubectl get ingress documentserver -o jsonpath="{.status.loadBalancer.ingress[*].ip}"
```

If the ingress IP is empty, try getting the `documentserver` ingress hostname:

```bash
$ kubectl get ingress documentserver -o jsonpath="{.status.loadBalancer.ingress[*].hostname}"
```

Associate the `documentserver` ingress IP or hostname with your domain name through your DNS provider.

After that, ONLYOFFICE Docs will be available at `https://your-domain-name/`.

### 6. Scale ONLYOFFICE Docs (optional)

*This step is optional. You can skip step [6](#6-scale-onlyoffice-docs-optional) entirely if you want to use default deployment settings.*

#### 6.1 Horizontal Pod Autoscaling

You can enable Autoscaling so that the number of replicas of `documentserver` deployment is calculated automatically based on the values and type of metrics.

For resource metrics, API metrics.k8s.io must be registered, which is generally provided by [metrics-server](https://github.com/kubernetes-sigs/metrics-server). It can be launched as a cluster add-on.

To use the target utilization value (`target.type==Utilization`), it is necessary that the values for `resources.requests` are specified in the deployment.

For more information about Horizontal Pod Autoscaling, see [here](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/).

To enable HPA for the `documentserver` deployment, specify the `documentserver.autoscaling.enabled=true` parameter. 
In this case, the `documentserver.replicas` parameter is ignored and the number of replicas is controlled by HPA.

With the `autoscaling.enabled` parameter enabled, by default Autoscaling will adjust the number of replicas based on the average percentage of CPU Utilization.
For other configurable Autoscaling parameters, see the [Parameters](#4-parameters) table.

#### 6.2 Manual scaling

Note: The `documentserver` deployments consist all the necessary dependencies in one pod.

To scale the `documentserver` deployment, use the following command:

```bash
$ kubectl scale -n default deployment documentserver --replicas=POD_COUNT
```

where `POD_COUNT` is a number of the `documentserver` pods.

### 7. Update ONLYOFFICE Docs

It's necessary to set the parameters for updating. For example,

```bash
$ helm upgrade documentserver onlyoffice/docs-shards \
  --set docservice.image.tag=[version]
```

  > **Note**: also need to specify the parameters that were specified during installation

Or modify the values.yaml file and run the command:

```bash
$ helm upgrade documentserver -f values.yaml onlyoffice/docs-shards
```

When the `helm upgrade` command is executed, replicas will be turned off one by one, and active documents on disabled replicas will be forced closed and saved. Also, disabled replicas will be removed from the Redis balancing tables.

### 8. Update ONLYOFFICE Docs license (optional)

In order to update the license, you need to perform the following steps:
 - Place the license.lic file containing the new key in some directory
 - Run the following commands:
```bash
$ kubectl delete secret license -n <NAMESPACE>
$ kubectl create secret generic license --from-file=path/to/license.lic -n <NAMESPACE>
```
 - Restart `documentserver` pods. For example, using the following command:
```bash
$ kubectl delete pod documentserver-*** -n <NAMESPACE>
```

### 9. ONLYOFFICE Docs installation test (optional)

You can test ONLYOFFICE Docs availability and access to connected dependencies by running the following command:

```bash
$ helm test documentserver -n <NAMESPACE>
```

The output should have the following line:

```bash
Phase: Succeeded
```

To view the log of the Pod running as a result of the `helm test` command, run the following command:

```bash
$ kubectl logs -f test-ds -n <NAMESPACE>
```

The ONLYOFFICE Docs availability check is considered a priority, so if it fails with an error, the test is considered to be failed.

After this, you can delete the `test-ds` Pod by running the following command:

```bash
$ kubectl delete pod test-ds -n <NAMESPACE>
```

Note: This testing is for informational purposes only and cannot guarantee 100% availability results.
It may be that even though all checks are completed successfully, an error occurs in the application.
In this case, more detailed information can be found in the application logs.

### 10. Access to the info page (optional)

The access to `/info` page is limited by default.
In order to allow the access to it, you need to specify the IP addresses or subnets (that will be Proxy container clients in this case) using `documentserver.proxy.infoAllowedIP` parameter.
Taking into consideration the specifics of Kubernetes net interaction it is possible to get the original IP of the user (being Proxy client) though it's not a standard scenario.
Generally the Pods / Nodes / Load Balancer addresses will actually be the clients, so these addresses are to be used.
In this case the access to the info page will be available to everyone.
You can further limit the access to the `info` page using Nginx [Basic Authentication](https://nginx.org/en/docs/http/ngx_http_auth_basic_module.html) which you can turn on by setting `documentserver.proxy.infoAllowedUser` parameter value and by setting the password using `documentserver.proxy.infoAllowedPassword` parameter, alternatively you can use the existing secret with password by setting its name with `documentserver.proxy.infoAllowedExistingSecret` parameter.

### 11. Deploy ONLYOFFICE Docs with your own dependency (optional)

### 11.1 Use your own nginx-ingress controller

**Note:** ONLYOFFICE Docs support **only** nginx-ingress controller [by the kubernetes](https://github.com/kubernetes/ingress-nginx). 

If you want to deploy ONLYOFFICE Docs in cluster where already exist nginx-ingress controller, please follow the step below.

**First of all** is to render two configMaps templates with `helm template` command, and apply them. This configMaps are needed for normal functioning of balancing requests between Docs shards.

**Note:** These config maps must be located in the same namespace as your deployment nginx-ingress controller. To ensure that the generated config maps will be deployed in the same namespace as your nginx-ingress controller, please set the parameter `documentserver.ingressCustomConfigMapsNamespace` if needed.

**Note:** When creating configMaps manually, check and change if necessary the parameters for connecting to Redis. 

> All available Redis connections parameters present [here](#4-parameters) with the `connections.` prefix

```bash
helm template docs onlyoffice/docs-shards --set documentserver.ingressCustomConfigMapsNamespace=<YOUR_INGRESS_NAMESPACE> --show-only templates/configmaps/balancer-snippet.yaml --show-only templates/configmaps/balancer-lua.yaml --dry-run=server > ./ingressConfigMaps.yaml 
```

**The second step**, apply configMaps that you create with command below:

```bash
$ kubectl apply -f ./ingressConfigMaps.yaml
```

**The third step**, Create PVC. Make new simple file with content presented below. PVC will be used for store ONLYOFFICE Docs static cache. Specify the same namespace where the controller is deployed:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nginx-ingress-pvc
  namespace: <controller-namespace>
spec:
  storageClassName: nfs
  accessModes:
    - ReadWriteMany
  volumeMode: Filesystem
  resources:
    requests:
      storage: 5Gi
```

Apply it with command:

```bash
$ kubectl apply -f ./<your-pvc-file-name>.yaml
```

**The four step**, you need to update your nginx-ingress controller deployment with new parameters.That will add volumes with the necessary configmaps that you just created. Follow the commands:

```bash
$ helm upgrade <INGRESS_RELEASE_NAME> ingress-nginx --repo https://kubernetes.github.io/ingress-nginx -n <INGRESS_NAMESPACE> -f https://raw.githubusercontent.com/ONLYOFFICE/Kubernetes-Docs-Shards/master/sources/ingress_values.yaml
```

**Now**, when your nginx-ingress controller if configure, you can deploy ONLYOFFICE Docs with command:

```bash
$ helm install docs onlyoffice/docs-shards --set ingress-nginx.enabled=false
```

## Using Grafana to visualize metrics (optional)

*This step is optional. You can skip this section if you don't want to install Grafana*

### 1. Deploy Grafana

Note: It is assumed that step [#6.2](#62-installing-prometheus) has already been completed.

#### 1.1 Deploy Grafana without installing ready-made dashboards

*You should skip step [#1.1](#11-deploy-grafana-without-installing-ready-made-dashboards) if you want to Deploy Grafana with the installation of ready-made dashboards*

To install Grafana to your cluster, run the following command:

```bash
$ helm install grafana bitnami/grafana \
  --set service.ports.grafana=80 \
  --set config.useGrafanaIniFile=true \
  --set config.grafanaIniConfigMap=grafana-ini \
  --set datasources.secretName=grafana-datasource
```

#### 1.2 Deploy Grafana with the installation of ready-made dashboards

#### 1.2.1 Installing ready-made Grafana dashboards

To install ready-made Grafana dashboards, set the `grafana.enabled` and `grafana.dashboard.enabled` parameters to `true`.
If ONLYOFFICE Docs is already installed you need to run the `helm upgrade documentserver onlyoffice/docs-shards --set grafana.enabled=true --set grafana.dashboard.enabled=true` command or `helm upgrade documentserver -f ./values.yaml onlyoffice/docs-shards` if the parameters are specified in the [values.yaml](values.yaml) file.
As a result, ready-made dashboards in the `JSON` format will be downloaded from the Grafana [website](https://grafana.com/grafana/dashboards),
the necessary edits will be made to them and configmap will be created from them. A dashboard will also be added to visualize metrics coming from the ONLYOFFICE Docs (it is assumed that step [#6](#6-deploy-statsd-exporter) has already been completed).

#### 1.2.2 Installing Grafana

To install Grafana to your cluster, run the following command:

```bash
$ helm install grafana bitnami/grafana \
  --set service.ports.grafana=80 \
  --set config.useGrafanaIniFile=true \
  --set config.grafanaIniConfigMap=grafana-ini \
  --set datasources.secretName=grafana-datasource \
  --set dashboardsProvider.enabled=true \
  --set dashboardsConfigMaps[0].configMapName=dashboard-node-exporter \
  --set dashboardsConfigMaps[0].fileName=dashboard-node-exporter.json \
  --set dashboardsConfigMaps[1].configMapName=dashboard-deployment \
  --set dashboardsConfigMaps[1].fileName=dashboard-deployment.json \
  --set dashboardsConfigMaps[2].configMapName=dashboard-redis \
  --set dashboardsConfigMaps[2].fileName=dashboard-redis.json \
  --set dashboardsConfigMaps[5].configMapName=dashboard-nginx-ingress \
  --set dashboardsConfigMaps[5].fileName=dashboard-nginx-ingress.json \
  --set dashboardsConfigMaps[6].configMapName=dashboard-documentserver \
  --set dashboardsConfigMaps[6].fileName=dashboard-documentserver.json \
  --set dashboardsConfigMaps[7].configMapName=dashboard-cluster-resourses \
  --set dashboardsConfigMaps[7].fileName=dashboard-cluster-resourses.json
```

After executing this command, the following dashboards will be imported into Grafana:

  - Node Exporter
  - Deployment Statefulset Daemonset
  - Redis Dashboard for Prometheus Redis Exporter
  - NGINX Ingress controller
  - ONLYOFFICE Docs
  - Resource usage by Pods and Containers

Note: You can see the description of the ONLYOFFICE Docs metrics that are visualized in Grafana [here](https://github.com/ONLYOFFICE/Kubernetes-Docs/wiki/Document-Server-Metrics).

See more details about installing Grafana via Helm [here](https://github.com/bitnami/charts/tree/master/bitnami/grafana).

### 2 Access to Grafana via Ingress

Note: It is assumed that step, please make sure that the nginx-ingress controller is installed in your cluster. If you already deploy ONLYOFFICE Docs and did not turn off the controller with the parameter `ingress-nginx.enabled=false` it is already present in the cluster.

If ONLYOFFICE Docs was installed with the parameter `grafana.ingress.enabled` (step [#5.2](#52-metrics-deployment-optional)) then access to Grafana will be at: `http://INGRESS-ADDRESS/grafana/`

If Ingres was installed using a secure connection (step [#5.3](#53-expose-onlyoffice-docs-via-https)), then access to Grafana will be at: `https://your-domain-name/grafana/`

### 3. View gathered metrics in Grafana

Go to the address `http(s)://your-domain-name/grafana/`

`Login - admin`

To get the password, run the following command:

```
$ kubectl get secret grafana-admin --namespace default -o jsonpath="{.data.GF_SECURITY_ADMIN_PASSWORD}" | base64 --decode
```

In the dashboard section, you will see the added dashboards that will display the metrics received from Prometheus.
