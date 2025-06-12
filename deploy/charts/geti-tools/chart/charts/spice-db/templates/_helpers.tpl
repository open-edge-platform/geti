{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "spice-db.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "spice-db.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "spice-db.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "spice-db.labels" -}}
chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "spice-db.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "spice-db.selectorLabels" -}}
{{- if .Values.fullnameOverride }}
app: {{ .Values.fullnameOverride | trunc 57 | trimSuffix "-" }}
{{- else }}
app: {{ .Chart.Name }}
{{- end }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
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
