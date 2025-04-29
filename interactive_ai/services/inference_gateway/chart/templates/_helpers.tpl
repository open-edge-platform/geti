{{/*
Expand the name of the chart.
*/}}
{{- define "inference-gateway.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "inference-gateway.fullname" -}}
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
{{- define "inference-gateway.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "inference-gateway.labels" -}}
helm.sh/chart: {{ include "inference-gateway.chart" . }}
{{ include "inference-gateway.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "inference-gateway.selectorLabels" -}}
app: {{ include "inference-gateway.name" . }}
app.kubernetes.io/name: {{ include "inference-gateway.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "inference-gateway.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "inference-gateway.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
This functions takes an array as input and appends each element to a new array
*/}}
{{- define "geti-common.appendToArray" -}}
{{- range $item := .sourceArray }}
    {{- $currentItem := printf "%s" $item }}
- {{ $currentItem | quote }}
{{- end }}
{{- end }}

{{/*
This function iterates over a structured variable containing key-value pairs and formats them into a list of YAML lines
*/}}
{{- define "geti-common.formatKeyValuePair" -}}
{{- range $item := .sourceDict }}
    {{- range $key, $value := $item }}
- {{ $key }}: {{ $value | quote }}
    {{- end }}
{{- end }}
{{- end }}
