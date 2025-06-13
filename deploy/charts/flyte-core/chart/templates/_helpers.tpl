{{/* vim: set filetype=mustache: */}}

{{- define "flyte.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flyte.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flyte.namespace" -}}
{{- default .Release.Namespace .Values.forceNamespace | trunc 63 | trimSuffix "-" -}}
{{- end -}}


{{- define "flyteadmin.name" -}}
flyteadmin
{{- end -}}

{{- define "jobs.name" -}}
{{- default "jobs" .Values.flyte_workflows.name }}
{{- end -}}

{{- define "flyteadmin.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flyteadmin.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "flyteadmin.labels" -}}
{{ include "flyteadmin.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "flytescheduler.name" -}}
flytescheduler
{{- end -}}

{{- define "flytescheduler.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flytescheduler.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}


{{- define "flytescheduler.labels" -}}
{{ include "flytescheduler.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "flyteclusterresourcesync.name" -}}
flyteclusterresourcesync
{{- end -}}

{{- define "flyteclusterresourcesync.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flyteclusterresourcesync.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "flyteclusterresourcesync.labels" -}}
{{ include "flyteclusterresourcesync.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "datacatalog.name" -}}
datacatalog
{{- end -}}

{{- define "datacatalog.selectorLabels" -}}
app.kubernetes.io/name: {{ template "datacatalog.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "datacatalog.labels" -}}
{{ include "datacatalog.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}


{{- define "flytepropeller.name" -}}
flytepropeller
{{- end -}}

{{- define "flytepropeller.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flytepropeller.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "flytepropeller.labels" -}}
{{ include "flytepropeller.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "flytepropeller-manager.name" -}}
flytepropeller-manager
{{- end -}}

{{- define "flytepropeller-manager.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flytepropeller-manager.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "flytepropeller-manager.labels" -}}
{{ include "flytepropeller-manager.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "flyte-pod-webhook.name" -}}
flyte-pod-webhook
{{- end -}}


{{- define "flyteconsole.name" -}}
flyteconsole
{{- end -}}

{{- define "flyteconsole.selectorLabels" -}}
app.kubernetes.io/name: {{ template "flyteconsole.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "flyteconsole.labels" -}}
{{ include "flyteconsole.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: flyte-core
{{- end -}}

{{- define "jobs.selectorLabels" -}}
app.kubernetes.io/name: {{ template "jobs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "jobs.labels" -}}
{{ include "jobs.selectorLabels" . }}
helm.sh/chart: {{ include "flyte.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app: jobs
{{- end -}}

# Optional blocks for secret mount

{{- define "databaseSecret.volume" -}}
{{- with .Values.common.databaseSecret.name -}}
- name: {{ . }}
  secret:
    secretName: {{ . }}
{{- end }}
{{- end }}

{{- define "databaseSecret.volumeMount" -}}
{{- with .Values.common.databaseSecret.name -}}
- mountPath: /etc/db
  name: {{ . }}
{{- end }}
{{- end }}

{{/*
Generate certificates for flyte
*/}}
{{- define "flyte.gen-certs" -}}
{{- $altNames := list ( printf "flyte-core.%s" .Release.Namespace ) ( printf "flyte-core.%s.svc" .Release.Namespace ) ( printf "flyte-pod-webhook.flyte" ) ( printf "flyte-pod-webhook.flyte.svc" ) -}}
{{- $ca := genCA "flyte-ca" 365 -}}
{{- $cert := genSignedCert ( include "flyte.name" . ) nil $altNames 365 $ca -}}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
ca.crt: {{ $ca.Cert | b64enc }}
{{- end -}}

{{- define "flyte.init-flyte-db-container" -}}
image: "{{ .Values.global.busybox.registry }}/{{ if .Values.global.busybox.repository }}{{ .Values.global.busybox.repository }}/{{ end }}{{ .Values.global.busybox.name }}"
securityContext:
  allowPrivilegeEscalation: false
  runAsNonRoot: true
  runAsUser: 10001
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
env:
- name: POSTGRES_HOST
  value: "impt-postgresql.{{ .Values.main_namespace }}"
- name: POSTGRES_PORT
  value: "5432"
- name: FLYTE_POSTGRES_USER
  valueFrom:
    secretKeyRef:
      name: impt-postgresql
      key: flyte-postgresql-username
- name: FLYTE_POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: impt-postgresql
      key: flyte-postgresql-password
- name: FLYTE_POSTGRES_DB
  valueFrom:
    configMapKeyRef:
      name: impt-postgresql
      key: flyte-postgresql-db
command: [ "/bin/sh", "-ecu" ]
args:
- |
  cp -RT /config-source /config-destination
  cat - > /config-destination/db.yaml <<EOF
  database:
    host: "$POSTGRES_HOST"
    port: "$POSTGRES_PORT"
    dbname: "$FLYTE_POSTGRES_DB"
    password: "$FLYTE_POSTGRES_PASSWORD"
    username: "$FLYTE_POSTGRES_USER"
    options: "{{ .Values.postgresql.options }}"
  EOF
{{- end -}}
