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

{{/*
Common labels
*/}}
{{- define "postgresql.labels" -}}
chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "postgresql.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "postgresql.selectorLabels" -}}
app: {{ .Chart.Name }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mongodb.labels" -}}
chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "mongodb.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mongodb.selectorLabels" -}}
app: {{ .Chart.Name }}
release: {{ .Release.Name }}
heritage: {{ .Release.Service }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mongodb.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mongodb.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

