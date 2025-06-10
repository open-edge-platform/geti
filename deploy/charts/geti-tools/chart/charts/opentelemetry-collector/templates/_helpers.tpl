{{/*
Expand the name of the chart.
*/}}
{{- define "opentelemetry-collector.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Get component name
*/}}
{{- define "opentelemetry-collector.component" -}}
{{- if eq .Values.mode "deployment" -}}
component: standalone-collector
{{- end -}}
{{- if eq .Values.mode "daemonset" -}}
component: agent-collector
{{- end -}}
{{- if eq .Values.mode "statefulset" -}}
component: statefulset-collector
{{- end -}}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "opentelemetry-collector.fullname" -}}
{{- printf "%s-%s" .Release.Namespace .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "opentelemetry-collector.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "opentelemetry-collector.labels" -}}
helm.sh/chart: {{ include "opentelemetry-collector.chart" . }}
{{ include "opentelemetry-collector.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "opentelemetry-collector.selectorLabels" -}}
app.kubernetes.io/name: {{ include "opentelemetry-collector.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "opentelemetry-collector.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "opentelemetry-collector.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}


{{/*
Create the name of the clusterRole to use
*/}}
{{- define "opentelemetry-collector.clusterRoleName" -}}
{{- if .Values.clusterRole.create }}
{{- default (include "opentelemetry-collector.fullname" .) .Values.clusterRole.name }}
{{- else }}
{{- default "default" .Values.clusterRole.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the clusterRoleBinding to use
*/}}
{{- define "opentelemetry-collector.clusterRoleBindingName" -}}
{{- if .Values.clusterRole.create }}
{{- default (include "opentelemetry-collector.fullname" .) .Values.clusterRole.clusterRoleBinding.name }}
{{- else }}
{{- default "default" .Values.clusterRole.clusterRoleBinding.name }}
{{- end }}
{{- end }}

{{/*
Return the appropriate apiVersion for ingress.
*/}}
{{- define "ingress.apiVersion" -}}
  {{- if and (.Capabilities.APIVersions.Has "networking.k8s.io/v1") (semverCompare ">= 1.19-0" .Capabilities.KubeVersion.Version) -}}
      {{- print "networking.k8s.io/v1" -}}
  {{- else if .Capabilities.APIVersions.Has "networking.k8s.io/v1beta1" -}}
    {{- print "networking.k8s.io/v1beta1" -}}
  {{- else -}}
    {{- print "extensions/v1beta1" -}}
  {{- end -}}
{{- end -}}

{{/*
Return if ingress supports pathType.
*/}}
{{- define "ingress.supportsPathType" -}}
  {{- or (eq (include "ingress.isStable" .) "true") (and (eq (include "ingress.apiVersion" .) "networking.k8s.io/v1beta1") (semverCompare ">= 1.18-0" .Capabilities.KubeVersion.Version)) -}}
{{- end -}}

{{/*
Return if ingress is stable.
*/}}
{{- define "ingress.isStable" -}}
  {{- eq (include "ingress.apiVersion" .) "networking.k8s.io/v1" -}}
{{- end -}}


{{- define "opentelemetry-collector.podAnnotations" -}}
{{- if .Values.podAnnotations }}
{{- .Values.podAnnotations | toYaml }}
{{- end }}
{{- end }}

{{- define "opentelemetry-collector.podLabels" -}}
{{- if .Values.podLabels }}
{{- .Values.podLabels | toYaml }}
{{- end }}
app: {{ .Chart.Name }}
{{- end }}

{{/*
Return the appropriate apiVersion for podDisruptionBudget.
*/}}
{{- define "podDisruptionBudget.apiVersion" -}}
  {{- if and (.Capabilities.APIVersions.Has "policy/v1") (semverCompare ">= 1.21-0" .Capabilities.KubeVersion.Version) -}}
    {{- print "policy/v1" -}}
  {{- else -}}
    {{- print "policy/v1beta1" -}}
  {{- end -}}
{{- end -}}


{{/*
Check if logs collection is enabled via deprecated "containerLogs" or "preset.logsCollection"
*/}}
{{- define "opentelemetry-collector.logsCollectionEnabled" }}
  {{- if eq (toString .Values.containerLogs) "<nil>" }}
    {{- print .Values.presets.logsCollection.enabled }}
  {{- else }}
    {{- print .Values.containerLogs.enabled }}
  {{- end }}
{{- end -}}
