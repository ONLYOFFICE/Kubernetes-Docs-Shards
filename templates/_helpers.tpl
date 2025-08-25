{{/*
Get the Redis password secret
*/}}
{{- define "ds.redis.secretName" -}}
{{- if or .Values.connections.redisPassword .Values.connections.redisNoPass -}}
    {{- printf "%s-%s" .Release.Name (include "ds.resources.name" (list . .Values.commonNameSuffix "redis")) -}}
{{- else if .Values.connections.redisExistingSecret -}}
    {{- printf "%s" (tpl .Values.connections.redisExistingSecret $) -}}
{{- end -}}
{{- end -}}

{{/*
Get the redis password
*/}}
{{- define "ds.redis.pass" -}}
{{- $redisSecret := include "ds.redis.secretName" . }}
{{- $secretKey := (lookup "v1" "Secret" .Release.Namespace $redisSecret).data }}
{{- $keyValue := (get $secretKey .Values.connections.redisSecretKeyName) | b64dec }}
{{- if .Values.connections.redisPassword -}}
    {{- printf "%s" .Values.connections.redisPassword -}}
{{- else if $keyValue -}}
    {{- printf "%s" $keyValue -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for Redis
*/}}
{{- define "ds.redis.createSecret" -}}
{{- if or .Values.connections.redisPassword .Values.connections.redisNoPass (not .Values.connections.redisExistingSecret) -}}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Return Redis password
*/}}
{{- define "ds.redis.password" -}}
{{- if not (empty .Values.connections.redisPassword) }}
    {{- .Values.connections.redisPassword }}
{{- else if .Values.connections.redisNoPass }}
    {{- printf "" }}
{{- else }}
    {{- required "A Redis Password is required!" .Values.connections.redisPassword }}
{{- end }}
{{- end -}}

{{/*
Get the Redis Sentinel password secret
*/}}
{{- define "ds.redis.sentinel.secretName" -}}
{{- if or .Values.connections.redisSentinelPassword .Values.connections.redisSentinelNoPass -}}
    {{- printf "%s-%s" .Release.Name (include "ds.resources.name" (list . .Values.commonNameSuffix "redis-sentinel")) -}}
{{- else if .Values.connections.redisSentinelExistingSecret -}}
    {{- printf "%s" (tpl .Values.connections.redisSentinelExistingSecret $) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for Redis Sentinel
*/}}
{{- define "ds.redis.sentinel.createSecret" -}}
{{- if or .Values.connections.redisSentinelPassword .Values.connections.redisSentinelNoPass (not .Values.connections.redisSentinelExistingSecret) -}}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the Redis Sentinel password
*/}}
{{- define "ds.redis.sentinel.pass" -}}
{{- $redisSecret := include "ds.redis.sentinel.secretName" . }}
{{- $secretKey := (lookup "v1" "Secret" .Release.Namespace $redisSecret).data }}
{{- $keyValue := (get $secretKey .Values.connections.redisSentinelSecretKeyName) | b64dec }}
{{- if .Values.connections.redisSentinelPassword -}}
    {{- printf "%s" .Values.connections.redisSentinelPassword -}}
{{- else if $keyValue -}}
    {{- printf "%s" $keyValue -}}
{{- end -}}
{{- end -}}

{{/*
Return Redis Sentinel password
*/}}
{{- define "ds.redis.sentinel.password" -}}
{{- if not (empty .Values.connections.redisSentinelPassword) }}
    {{- .Values.connections.redisSentinelPassword }}
{{- else if .Values.connections.redisSentinelNoPass }}
    {{- printf "" }}
{{- else }}
    {{- required "A Redis Sentinel Password is required!" .Values.connections.redisSentinelPassword }}
{{- end }}
{{- end -}}

{{/*
Get the info auth password secret
*/}}
{{- define "ds.info.secretName" -}}
{{- if .Values.documentserver.proxy.infoAllowedExistingSecret -}}
    {{- printf "%s" (tpl .Values.documentserver.proxy.infoAllowedExistingSecret $) -}}
{{- else if .Values.documentserver.proxy.infoAllowedUser -}}
    {{- printf "%s-%s" .Release.Name (include "ds.resources.name" (list . .Values.commonNameSuffix "info-auth")) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for info auth
*/}}
{{- define "ds.info.createSecret" -}}
{{- if and .Values.documentserver.proxy.infoAllowedUser (not .Values.documentserver.proxy.infoAllowedExistingSecret) -}}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the secure link secret name
*/}}
{{- define "ds.secureLinkSecret.secretName" -}}
{{- if .Values.documentserver.proxy.secureLinkExistingSecret -}}
    {{- printf "%s" (tpl .Values.documentserver.proxy.secureLinkExistingSecret $) -}}
{{- else -}}
    {{- printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix "link-secret")) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for secure link
*/}}
{{- define "ds.secureLinkSecret.createSecret" -}}
{{- if empty .Values.documentserver.proxy.secureLinkExistingSecret }}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the PVC name
*/}}
{{- define "ds.pvc.name" -}}
{{- $context := index . 0 -}}
{{- $pvcExistingClaim := index . 1 -}}
{{- $pvcName := index . 2 -}}
{{- if $pvcExistingClaim -}}
    {{- printf "%s" (tpl $pvcExistingClaim $context) -}}
{{- else }}
    {{- printf "%s" (include "ds.resources.name" (list $context $context.Values.commonNameSuffix $pvcName)) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a pvc object for ds-service-files should be created
*/}}
{{- define "ds.pvc.create" -}}
{{- if empty . }}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the license name
*/}}
{{- define "ds.license.secretName" -}}
{{- if .Values.license.existingSecret -}}
    {{- printf "%s" (tpl .Values.license.existingSecret $) -}}
{{- else }}
    {{- printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix "license")) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for license
*/}}
{{- define "ds.license.createSecret" -}}
{{- if and (empty .Values.license.existingSecret) (empty .Values.license.existingClaim) }}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the jwt name
*/}}
{{- define "ds.jwt.secretName" -}}
{{- if .Values.jwt.existingSecret -}}
    {{- printf "%s" (tpl .Values.jwt.existingSecret $) -}}
{{- else }}
    {{- printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix "jwt")) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a secret object should be created for jwt
*/}}
{{- define "ds.jwt.createSecret" -}}
{{- if empty .Values.jwt.existingSecret }}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Get the service name for ds
*/}}
{{- define "ds.svc.name" -}}
{{- if not (empty .Values.customBalancer.service.existing) }}
    {{- printf "%s" (tpl .Values.customBalancer.service.existing $) -}}
{{- else if empty .Values.customBalancer.service.existing }}
    {{- printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix "docs-balancer")) -}}
{{- else }}
    {{- printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix "documentserver")) -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a balancer service object should be created for ds
*/}}
{{- define "balancer.svc.create" -}}
{{- if empty .Values.customBalancer.service.existing }}
    {{- true -}}
{{- end -}}
{{- end -}}

{{/*
Return balancer shutdown timer
*/}}
{{- define "balancer.shutdown.timer" -}}
{{- if le (int .Values.customBalancer.terminationGracePeriodSeconds) 60 -}}
    {{- printf "70" -}}
{{- else }}
    {{- printf "%s" .Values.customBalancer.terminationGracePeriodSeconds -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds labels
*/}}
{{- define "ds.labels.commonLabels" -}}
{{- range $key, $value := .Values.commonLabels }}
{{ $key }}: {{ tpl $value $ }}
{{- end }}
{{- end -}}

{{/*
Get the ds annotations
*/}}
{{- define "ds.annotations.commonAnnotations" -}}
{{- $annotations := toYaml .keyName }}
{{- if contains "{{" $annotations }}
    {{- tpl $annotations .context }}
{{- else }}
    {{- $annotations }}
{{- end }}
{{- end -}}

{{/*
Get the update strategy type for ds
*/}}
{{- define "ds.update.strategyType" -}}
{{- if eq .type "RollingUpdate" -}}
    {{- toYaml . | nindent 4 -}}
{{- else -}}
    {{- omit . "rollingUpdate" | toYaml | nindent 4 -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds Service Account name
*/}}
{{- define "ds.serviceAccountName" -}}
{{- $saName := default "default" .Values.serviceAccount.name }}
{{- if .Values.serviceAccount.create -}}
    {{ default (printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix .Release.Name))) (printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix $saName))) }}
{{- else -}}
    {{ printf "%s" (include "ds.resources.name" (list . .Values.commonNameSuffix $saName)) }}
{{- end -}}
{{- end -}}

{{/*
Get the ds Resource name
*/}}
{{- define "ds.resources.name" -}}
{{- $context := index . 0 -}}
{{- $suffixName := index . 1 -}}
{{- $resourceName := index . 2 -}}
{{- if $suffixName -}}
    {{- printf "%s-%s" $resourceName (tpl $suffixName $context) -}}
{{- else -}}
    {{- printf "%s" $resourceName -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds Namespace
*/}}
{{- define "ds.namespace" -}}
{{- if .Values.namespaceOverride -}}
    {{- .Values.namespaceOverride -}}
{{- else -}}
    {{- .Release.Namespace -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds Grafana Namespace
*/}}
{{- define "ds.grafana.namespace" -}}
{{- if .Values.grafana.namespace -}}
    {{- .Values.grafana.namespace -}}
{{- else if .Values.namespaceOverride -}}
    {{- .Values.namespaceOverride -}}
{{- else -}}
    {{- .Release.Namespace -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds virtual path with trailing slash
/                   -> /
/path               -> /path/
/path/              -> /path/
/path/path          -> /path/path/
/path/path/         -> /path/path/
/path(/|$)(.*)      -> /path(/|$)(.*)
/path/path(/|$)(.*) -> /path/path(/|$)(.*)
*/}}
{{- define "ds.path.withTrailingSlash" -}}
{{- $pathValue := . -}}
{{- if hasSuffix "/" $pathValue -}}
    {{- printf "%s" $pathValue -}}
{{- else if hasSuffix "(/|$)(.*)" $pathValue -}}
    {{- printf "%s" $pathValue -}}
{{- else -}}
    {{- printf "%s/" $pathValue -}}
{{- end -}}
{{- end -}}

{{/*
Get the ds virtual path without trailing slash
/                   -> /
/path               -> /path
/path/              -> /path
/path/path          -> /path/path
/path/path/         -> /path/path
/path(/|$)(.*)      -> /path
/path/path(/|$)(.*) -> /path/path
*/}}
{{- define "ds.path.withoutTrailingSlash" -}}
{{- $pathValue := . -}}
{{- if hasSuffix "(/|$)(.*)" $pathValue -}}
    {{- $pathValue = trimSuffix "(/|$)(.*)" $pathValue -}}
{{- end -}}
{{- trimSuffix "/" $pathValue | default "/" -}}
{{- end -}}

{{/*
Get ds url
*/}}
{{- define "ds.dsUrl" -}}
{{- if not (hasSuffix "/" .) -}}
  {{- printf "%s/" . -}}
{{- else }}
  {{- printf "%s" . -}}
{{- end -}}
{{- end -}}

{{/*
Get ds url for example
*/}}
{{- define "ds.example.dsUrl" -}}
{{- $pathInput := (tpl .Values.example.dsUrl $) -}}
{{- if eq $pathInput "/" -}}
  {{- if .Values.ingress.enabled -}}
    {{- $pathInput = .Values.ingress.path -}}
  {{- end -}}
  {{- if hasSuffix "(/|$)(.*)" $pathInput -}}
    {{- $pathInput = trimSuffix "(/|$)(.*)" $pathInput -}}
    {{- include "ds.dsUrl" $pathInput -}}
  {{- else }}
    {{- include "ds.dsUrl" $pathInput -}}
  {{- end -}}
{{- else }}
  {{- include "ds.dsUrl" $pathInput -}}
{{- end -}}
{{- end -}}

{{/*
Get the Secret value
*/}}
{{- define "ds.secrets.lookup" -}}
{{- $context := index . 0 -}}
{{- $existValue := index . 1 -}}
{{- $getSecretName := index . 2 -}}
{{- $getSecretKey := index . 3 -}}
{{- if not $existValue }}
    {{- $secret_lookup := (lookup "v1" "Secret" $context.Release.Namespace $getSecretName).data }}
    {{- $getSecretValue := (get $secret_lookup $getSecretKey) | b64dec }}
    {{- if $getSecretValue -}}
        {{- printf "%s" $getSecretValue -}}
    {{- else -}}
        {{- printf "%s" (randAlpha 16) -}}
    {{- end -}}
{{- else -}}
    {{- printf "%s" $existValue -}}
{{- end -}}
{{- end -}}
