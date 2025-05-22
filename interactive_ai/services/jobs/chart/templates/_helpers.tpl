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
Jobs microservice name.
*/}}
{{- define "jobs-ms.name" -}}
{{- $ms_name := printf "%s-ms" .Chart.Name -}}
{{- default $ms_name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Jobs scheduler name.
*/}}
{{- define "jobs-scheduler.name" -}}
{{- $scheduler_name := printf "%s-scheduler" .Chart.Name -}}
{{- default $scheduler_name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Jobs scheduling policy service name.
*/}}
{{- define "jobs-scheduling-policy.name" -}}
{{- $scheduling_policy_name := printf "%s-scheduling-policy" .Chart.Name -}}
{{- default $scheduling_policy_name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jobs.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Jobs microservice labels
*/}}
{{- define "jobs-ms.labels" -}}
helm.sh/chart: {{ include "jobs.chart" . }}
{{ include "jobs-ms.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Jobs microservice selector labels
*/}}
{{- define "jobs-ms.selectorLabels" -}}
app: {{ include "jobs-ms.name" . }}
app.kubernetes.io/name: {{ include "jobs-ms.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Jobs scheduler labels
*/}}
{{- define "jobs-scheduler.labels" -}}
helm.sh/chart: {{ include "jobs.chart" . }}
{{ include "jobs-scheduler.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Jobs scheduler selector labels
*/}}
{{- define "jobs-scheduler.selectorLabels" -}}
app: {{ include "jobs-scheduler.name" . }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
{{- end }}

{{/*
Jobs scheduling policy service labels
*/}}
{{- define "jobs-scheduling-policy.labels" -}}
helm.sh/chart: {{ include "jobs.chart" . }}
{{ include "jobs-scheduling-policy.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Jobs scheduling policy service selector labels
*/}}
{{- define "jobs-scheduling-policy.selectorLabels" -}}
app: {{ include "jobs-scheduling-policy.name" . }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
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
