{{/* vim: set filetype=mustache: */}}
{{/*
Expand the name of the chart.
*/}}
{{- define "cert-manager-istio-csr.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "cert-manager-istio-csr.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "cert-manager-istio-csr.labels" -}}
app.kubernetes.io/name: {{ include "cert-manager-istio-csr.name" . }}
helm.sh/chart: {{ include "cert-manager-istio-csr.chart" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- if .Values.commonLabels }}
{{ toYaml .Values.commonLabels }}
{{- end }}
{{- end -}}

{{/*
Util function for generating the image URL based on the provided options.
IMPORTANT: This function is standarized across all charts in the cert-manager GH organization.
Any changes to this function should also be made in cert-manager, trust-manager, approver-policy, ...
See https://github.com/cert-manager/cert-manager/issues/6329 for a list of linked PRs.
*/}}
{{- define "image" -}}
{{- $defaultTag := index . 1 -}}
{{- with index . 0 -}}
{{- if .registry -}}{{ printf "%s/%s/%s" .registry .repository .name }}{{- else -}}{{- .repository -}}{{- end -}}
{{- end }}
{{- end }}

{{/*
Runtime config name
*/}}
{{- define "cert-manager-istio-csr.runtimeConfigurationName" -}}
{{- if .Values.app.runtimeConfiguration.name -}}
    {{- .Values.app.runtimeConfiguration.name -}}
{{- else if .Values.app.runtimeIssuanceConfigMap -}}
    {{- .Values.app.runtimeIssuanceConfigMap -}}
{{- else if .Values.app.runtimeConfiguration.create -}}
    {{ include "cert-manager-istio-csr.name" . }}
{{- end -}}
{{- end }}