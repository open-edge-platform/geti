{{/*
Expand the name of the chart.
*/}}
{{- define "seaweed-fs.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "seaweed-fs.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Namespace }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Namespace $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "seaweed-fs.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "seaweed-fs.labels" -}}
helm.sh/chart: {{ include "seaweed-fs.chart" . }}
{{ include "seaweed-fs.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "seaweed-fs.selectorLabels" -}}
app: {{ include "seaweed-fs.name" . }}
app.kubernetes.io/name: {{ include "seaweed-fs.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "seaweed-fs.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "seaweed-fs.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{- define "flyteworkflow.domain" -}}
{{.Values.flyte_workflows.domain }}
{{- end -}}

{{- define "flyteworkflow.name" }}
{{- .Values.main_namespace }}-{{ .Values.flyte_workflows.name }}
{{- end -}}

{{- define "flyteworkflow.namespace" }}
{{- .Values.main_namespace }}-{{ .Values.flyte_workflows.name }}-{{ include "flyteworkflow.domain" . }}
{{- end -}}