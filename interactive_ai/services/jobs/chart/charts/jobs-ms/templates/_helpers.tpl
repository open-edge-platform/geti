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
Expand the name of the chart.
*/}}
{{- define "jobs-ms.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "jobs-ms.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "jobs-ms.labels" -}}
helm.sh/chart: {{ include "jobs-ms.chart" . }}
{{ include "jobs-ms.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "jobs-ms.selectorLabels" -}}
app: {{ include "jobs-ms.name" . }}
app.kubernetes.io/name: {{ include "jobs-ms.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
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
