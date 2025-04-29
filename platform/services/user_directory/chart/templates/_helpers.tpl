{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "user-directory.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "user-directory.fullname" -}}
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
{{- define "user-directory.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "user-directory.labels" -}}
helm.sh/chart: {{ include "user-directory.chart" . }}
{{ include "user-directory.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "user-directory.selectorLabels" -}}
app.kubernetes.io/name: {{ include "user-directory.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
This functions takes an array as input and appends each element to a new array
*/}}
{{- define "user-directory.appendToArray" -}}
{{- range $item := .sourceArray }}
    {{- $currentItem := printf "%s" $item }}
- {{ $currentItem | quote }}
{{- end }}
{{- end }}

{{/*
This function iterates over a structured variable containing key-value pairs and formats them into a list of YAML lines
*/}}
{{- define "user-directory.formatKeyValuePair" -}}
{{- range $item := .sourceDict }}
    {{- range $key, $value := $item }}
- {{ $key }}: {{ $value | quote }}
    {{- end }}
{{- end }}
{{- end }}
