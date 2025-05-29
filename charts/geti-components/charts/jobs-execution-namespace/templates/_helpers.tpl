{{/* vim: set filetype=mustache: */}}

{{- define "flyteworkflow.domain" -}}
{{.Values.flyte_workflows.domain }}
{{- end -}}

{{- define "flyteworkflow.name" }}
{{- .Values.main_namespace }}-{{ .Values.flyte_workflows.name }}
{{- end -}}

{{- define "flyteworkflow.namespace" }}
{{- .Values.main_namespace }}-{{ .Values.flyte_workflows.name }}-{{ include "flyteworkflow.domain" . }}
{{- end -}}
