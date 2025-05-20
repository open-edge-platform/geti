{{/* vim: set filetype=mustache: */}}

{{/*
Return the credentials secret
*/}}
{{- define "spice-db.secretName" -}}
    {{- printf "%s-spice-db" .Release.Namespace }}
{{- end -}}

{{/*
Return the TLS secret
*/}}
{{- define "spice-db.tlsSecretName" -}}
    {{- printf "%s-spice-db-tls" .Release.Namespace }}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "jobs-scheduler.labels" -}}
chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "jobs-scheduler.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jobs-scheduler.selectorLabels" -}}
app: {{ .Chart.Name }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
{{- end }}
