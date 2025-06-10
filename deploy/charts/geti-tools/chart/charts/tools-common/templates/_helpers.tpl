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
Return the Kafka JAAS credentials secret
*/}}
{{- define "kafka.jaasSecretName" -}}
    {{- printf "%s-kafka-jaas" .Release.Namespace -}}
{{- end -}}

{{/*
This functions takes an array as input and appends each element to a new array
*/}}
{{- define "tools-common.appendToArray" -}}
{{- range $item := .sourceArray }}
    {{- $currentItem := printf "%s" $item }}
- {{ $currentItem | quote }}
{{- end }}
{{- end }}

{{/*
This function iterates over a structured variable containing key-value pairs and formats them into a list of YAML lines
*/}}
{{- define "tools-common.formatKeyValuePair" -}}
{{- range $item := .sourceDict }}
    {{- range $key, $value := $item }}
- {{ $key }}: {{ $value | quote }}
    {{- end }}
{{- end }}
{{- end }}
