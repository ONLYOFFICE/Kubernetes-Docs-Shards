# Changelog

## 3.1.0

### New Features

* Added the ability to connect to Redis Cluster
* Added Retry when connecting to Redis
* Added the ability to specify multiple hostname for Ingress
* Added the ability to set up the certificate request in Let's Encrypt
* Added the ability to use custom user dictionaries

### Changes

* Released ONLYOFFICE Docs [v9.0.3](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#903)

### Fixes

* Fixed Redis Sentinel connection error in initialization and key cleanup scripts when deleting a shard if multiple Sentinel nodes are specified

## 3.0.0

### New Features

* Added the ability to connect to multiple Redis Sentinel nodes
* Added the ability to specify an existing Secret for Proxy `secure_link`
* Added the creation of a PVC to store a shared runtime config. You can specify an existing PVC
* Added the ability to set up the `hostAliases`

### Changes

* Released ONLYOFFICE Docs [v9.0.2](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#902)
* Balancer container is run by user with `ds(101:101)` permissions

## 2.1.3

### Changes

* Released ONLYOFFICE Docs [v8.3.3](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#833)

## 2.1.2

### Changes

* Released ONLYOFFICE Docs [v8.3.2](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#832)

## 2.1.1

### Changes

* Released ONLYOFFICE Docs [v8.3.1](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#831)

## 2.1.0

### New Features

* Added the ability to connect to Redis Sentinel
* Enabled the option to configure keepalive for Redis connections
* Introduced a observer service in the Balancer that detects configuration changes and restarts the Nginx worker process accordingly
* Implemented a `preStop` hook in the Balancer to ensure proper termination of processes when a container is stopped within a Pod
* Added the ability to adjust the logging level in the Balancer
* Added `Probes` for the Balancer
* Introduced a `pre-upgrade` Job to clean up files and directories from previous DS versions
* Implemented a patch for DS replicas (Shards) using the `pod-deletion-cost` annotation, which contains the number of active connections to each replica. This allows for a prioritized replicas termination sequence during upgrades
* Added a `pre-delete` Job to gracefully disconnect a Shards before deleting the Helm release
* Added the ability to automatically generate WOPI keys during installation or upgrades, or to use existing ones

### Changes

* Changed the scheme for balancing new requests to documentserver replicas when upgrading the version
* The values of the parameters `jwt.secret`, `proxy.secureLinkSecret`, and `proxy.infoAllowedPassword` have been replaced with empty values instead of default ones, with the option to either generate random values or use the provided value
* Released ONLYOFFICE Docs [v8.3.0](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#830)

## 2.0.2

### Changes

* Released ONLYOFFICE Docs [v8.2.2](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#822)

## 2.0.1

### Changes

* Released ONLYOFFICE Docs [v8.2.1](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#821)

## 2.0.0

### New Features

* Added request routing based on Docs version during updates
* Added a signal control processing handler as the first process in Docs containers

### Changes

* Requests load balancing mechanism has been redesigned
* Pod remains in `Terminating` status while documents are being edited on it until `terminationGracePeriodSeconds` expires
* Released ONLYOFFICE Docs [v8.2.0](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#820)

## 1.0.1

### Changes

* Released ONLYOFFICE Docs [v8.1.3](https://github.com/ONLYOFFICE/DocumentServer/blob/master/CHANGELOG.md#813)

## 1.0.0

* Initial release
