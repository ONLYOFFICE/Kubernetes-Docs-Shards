{{/*
Get the Redis password secret
*/}}
{{- define "ds.redis.secretName" -}}
{{- if or .Values.connections.redisPassword .Values.connections.redisNoPass -}}
    {{- printf "%s-redis" .Release.Name -}}
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
Get the info auth password secret
*/}}
{{- define "ds.info.secretName" -}}
{{- if .Values.documentserver.proxy.infoAllowedExistingSecret -}}
    {{- printf "%s" (tpl .Values.documentserver.proxy.infoAllowedExistingSecret $) -}}
{{- else if .Values.documentserver.proxy.infoAllowedPassword -}}
    {{- printf "%s-info-auth" .Release.Name -}}
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
Return info auth password
*/}}
{{- define "ds.info.password" -}}
{{- if not (empty .Values.documentserver.proxy.infoAllowedPassword) }}
    {{- .Values.documentserver.proxy.infoAllowedPassword }}
{{- else }}
    {{- required "A info auth Password is required!" .Values.documentserver.proxy.infoAllowedPassword }}
{{- end }}
{{- end -}}

{{/*
Get the PVC name
*/}}
{{- define "ds.pvc.name" -}}
{{- if .Values.persistence.existingClaim -}}
    {{- printf "%s" (tpl .Values.persistence.existingClaim $) -}}
{{- else }}
    {{- printf "ds-service-files" -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a pvc object should be created
*/}}
{{- define "ds.pvc.create" -}}
{{- if empty .Values.persistence.existingClaim }}
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
    {{- printf "license" -}}
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
    {{- printf "jwt" -}}
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
{{- if .Values.service.existing -}}
    {{- printf "%s" (tpl .Values.service.existing $) -}}
{{- else }}
    {{- printf "documentserver" -}}
{{- end -}}
{{- end -}}

{{/*
Return true if a service object should be created for ds
*/}}
{{- define "ds.svc.create" -}}
{{- if empty .Values.service.existing }}
    {{- true -}}
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
Get the ds Service Account name
*/}}
{{- define "ds.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
    {{ default .Release.Name .Values.serviceAccount.name }}
{{- else -}}
    {{ default "default" .Values.serviceAccount.name }}
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
Get the ds virtual path
*/}}
{{- define "ds.ingress.path" -}}
{{- if eq .Values.ingress.path "/" -}}
    {{- printf "/" -}}
{{- else }}
    {{- printf "%s(/|$)(.*)" .Values.ingress.path -}}
{{- end -}}
{{- end -}}

{{/*
Get ds url for example
*/}}
{{- define "ds.example.dsUrl" -}}
{{- if and (ne .Values.ingress.path "/") (eq .Values.example.dsUrl "/") -}}
    {{- printf "%s/" (tpl .Values.ingress.path $) -}}
{{- else }}
    {{- printf "%s" (tpl .Values.example.dsUrl $) -}}
{{- end -}}
{{- end -}}
