{{- define "opentelemetry-collector.baseConfig" -}}
{{- $processorsConfig := get .Values.config "processors" }}
{{- .Values.config | toYaml }}
{{- end }}

{{/*
Merge user supplied config into memory ballast config.
*/}}
{{- define "opentelemetry-collector.ballastConfig" -}}
{{- $memoryBallastConfig := get .Values.config.extensions "memory_ballast" }}
{{- if or (not $memoryBallastConfig) (not $memoryBallastConfig.size_mib) }}
{{- $_ := set $memoryBallastConfig "size_mib" (include "opentelemetry-collector.getMemBallastSizeMib" .Values.resources.limits.memory) }}
{{- end }}
{{- .Values.config | toYaml }}
{{- end }}

{{/*
Build config file for daemonset OpenTelemetry Collector
*/}}
{{- define "opentelemetry-collector.daemonsetConfig" -}}
{{- $values := deepCopy .Values }}
{{- $data := dict "Values" $values | mustMergeOverwrite (deepCopy .) }}
{{- $config := include "opentelemetry-collector.baseConfig" $data | fromYaml }}
{{- $config := include "opentelemetry-collector.ballastConfig" $data | fromYaml | mustMergeOverwrite $config }}
{{- if eq (include "opentelemetry-collector.logsCollectionEnabled" .) "true" }}
{{- $config = (include "opentelemetry-collector.applyLogsCollectionConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.hostMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyHostMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.kubeletMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyKubeletMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.kubernetesAttributes.enabled }}
{{- $config = (include "opentelemetry-collector.applyKubernetesAttributesConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.clusterMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyClusterMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.global.grafana_enabled }}
{{- $config = (include "opentelemetry-collector.applyGrafanaStackConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- tpl (toYaml $config) . }}
{{- end }}

{{/*
Build config file for deployment OpenTelemetry Collector
*/}}
{{- define "opentelemetry-collector.deploymentConfig" -}}
{{- $values := deepCopy .Values }}
{{- $data := dict "Values" $values | mustMergeOverwrite (deepCopy .) }}
{{- $config := include "opentelemetry-collector.baseConfig" $data | fromYaml }}
{{- if eq (include "opentelemetry-collector.logsCollectionEnabled" .) "true" }}
{{- $config = (include "opentelemetry-collector.applyLogsCollectionConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.hostMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyHostMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.kubeletMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyKubeletMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.kubernetesAttributes.enabled }}
{{- $config = (include "opentelemetry-collector.applyKubernetesAttributesConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.presets.clusterMetrics.enabled }}
{{- $config = (include "opentelemetry-collector.applyClusterMetricsConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- if .Values.global.grafana_enabled }}
{{- $config = (include "opentelemetry-collector.applyGrafanaStackConfig" (dict "Values" $data "config" $config) | fromYaml) }}
{{- end }}
{{- $config = (include "opentelemetry-collector.applyPrometheusKubernetesPodsReceiver" (dict "Values" $data "config" $config) | fromYaml) -}}
{{- tpl (toYaml $config) . }}
{{- end }}

{{/*
Convert memory value from resources.limit to numeric value in MiB to be used by otel memory_limiter processor.
*/}}
{{- define "opentelemetry-collector.convertMemToMib" -}}
{{- $mem := lower . -}}
{{- if hasSuffix "e" $mem -}}
{{- trimSuffix "e" $mem | atoi | mul 1000 | mul 1000 | mul 1000 | mul 1000 -}}
{{- else if hasSuffix "ei" $mem -}}
{{- trimSuffix "ei" $mem | atoi | mul 1024 | mul 1024 | mul 1024 | mul 1024 -}}
{{- else if hasSuffix "p" $mem -}}
{{- trimSuffix "p" $mem | atoi | mul 1000 | mul 1000 | mul 1000 -}}
{{- else if hasSuffix "pi" $mem -}}
{{- trimSuffix "pi" $mem | atoi | mul 1024 | mul 1024 | mul 1024 -}}
{{- else if hasSuffix "t" $mem -}}
{{- trimSuffix "t" $mem | atoi | mul 1000 | mul 1000 -}}
{{- else if hasSuffix "ti" $mem -}}
{{- trimSuffix "ti" $mem | atoi | mul 1024 | mul 1024 -}}
{{- else if hasSuffix "g" $mem -}}
{{- trimSuffix "g" $mem | atoi | mul 1000 -}}
{{- else if hasSuffix "gi" $mem -}}
{{- trimSuffix "gi" $mem | atoi | mul 1024 -}}
{{- else if hasSuffix "m" $mem -}}
{{- div (trimSuffix "m" $mem | atoi | mul 1000) 1024 -}}
{{- else if hasSuffix "mi" $mem -}}
{{- trimSuffix "mi" $mem | atoi -}}
{{- else if hasSuffix "k" $mem -}}
{{- div (trimSuffix "k" $mem | atoi) 1000 -}}
{{- else if hasSuffix "ki" $mem -}}
{{- div (trimSuffix "ki" $mem | atoi) 1024 -}}
{{- else -}}
{{- div (div ($mem | atoi) 1024) 1024 -}}
{{- end -}}
{{- end -}}

{{/*
Get otel memory_limiter limit_mib value based on 80% of resources.memory.limit.
*/}}
{{- define "opentelemetry-collector.getMemLimitMib" -}}
{{- div (mul (include "opentelemetry-collector.convertMemToMib" .) 80) 100 }}
{{- end -}}

{{/*
Get otel memory_limiter spike_limit_mib value based on 25% of resources.memory.limit.
*/}}
{{- define "opentelemetry-collector.getMemSpikeLimitMib" -}}
{{- div (mul (include "opentelemetry-collector.convertMemToMib" .) 25) 100 }}
{{- end -}}

{{/*
Get otel memory_limiter ballast_size_mib value based on 40% of resources.memory.limit.
*/}}
{{- define "opentelemetry-collector.getMemBallastSizeMib" }}
{{- div (mul (include "opentelemetry-collector.convertMemToMib" .) 40) 100 }}
{{- end -}}

{{- define "opentelemetry-collector.applyHostMetricsConfig" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.hostMetricsConfig" .Values | fromYaml) .config }}
{{- $_ := set (index $config "service" "pipelines" "metrics/k8s") "receivers" (append (index $config "service" "pipelines" "metrics/k8s" "receivers") "hostmetrics" | uniq)  }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.hostMetricsConfig" -}}
receivers:
  hostmetrics:
    collection_interval: 10s
    scrapers:
        cpu:
        load:
        memory:
        disk:
        filesystem:
        network:
{{- end }}

{{- define "opentelemetry-collector.applyClusterMetricsConfig" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.clusterMetricsConfig" .Values | fromYaml) .config }}
{{- $_ := set (index $config "service" "pipelines" "metrics/k8s") "receivers" (append (index $config "service" "pipelines" "metrics/k8s" "receivers") "k8s_cluster" | uniq)  }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.clusterMetricsConfig" -}}
receivers:
  k8s_cluster:
    collection_interval: 10s
{{- end }}

{{- define "opentelemetry-collector.applyKubeletMetricsConfig" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.kubeletMetricsConfig" .Values | fromYaml) .config }}
{{- $_ := set (index $config "service" "pipelines" "metrics/k8s") "receivers" (append (index $config "service" "pipelines" "metrics/k8s" "receivers") "kubeletstats" | uniq)  }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.kubeletMetricsConfig" -}}
receivers:
  kubeletstats:
    collection_interval: 60s
    auth_type: "serviceAccount"
    endpoint: "${K8S_NODE_NAME}:10250"
    insecure_skip_verify: false
    extra_metadata_labels:
    - container.id
    - k8s.volume.type
    metric_groups:
    - node
    - pod
    - container
    - volume
{{- end }}

{{- define "opentelemetry-collector.applyPrometheusKubernetesPodsReceiver" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.prometheusKubernetesPodsReceiver" .Values | fromYaml) .config }}
{{- $_ := set (index $config "service" "pipelines" "metrics/k8s") "receivers" (append (index $config "service" "pipelines" "metrics/k8s" "receivers") "prometheus/kubernetes_pods" | uniq)  }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.prometheusKubernetesPodsReceiver" -}}
receivers:
  prometheus/kubernetes_pods:
    config:
      scrape_configs:
      - job_name: kubernetes-service-discovery
        scrape_interval: 60s
        scrape_timeout: 60s
        static_configs:
          - targets:
            - modelmesh-serving:2112
            {{- if .Values.global.dcgm_dashboard }}
            - {{ .Release.Name }}-dcgm-exporter:9400
            {{- else if .Values.global.xpum_dashboard }}
            - {{ .Release.Name }}-xpu-manager:29999
            {{- end -}}
{{- end -}}

{{- define "opentelemetry-collector.applyLogsCollectionConfig" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.logsCollectionConfig" .Values | fromYaml) .config }}
{{/* Append filelog receiver to logs/geti pipeline receivers */}}
{{- $_ := set (index $config "service" "pipelines" "logs/geti/file") "receivers" (append (index $config "service" "pipelines" "logs/geti/file" "receivers") "filelog" | uniq)  }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.logsCollectionConfig" -}}
receivers:
  filelog:
    include: [ /var/log/pods/*/*/*.log ]
    {{- if .Values.presets.logsCollection.includeCollectorLogs }}
{{/*    excluding logs from istio-proxy sidecars */}}
    exclude: [ /var/log/pods/*/istio-proxy/*.log ]
    {{- else }}
    # Exclude collector container's logs. The file format is /var/log/pods/<namespace_name>_<pod_name>_<pod_uid>/<container_name>/<run_id>.log
    exclude: [ /var/log/pods/{{ .Release.Namespace }}_{{ include "opentelemetry-collector.fullname" . }}*_*/{{ .Chart.Name }}/*.log, /var/log/pods/*/istio-proxy/*.log ]
    {{- end }}
    start_at: beginning
    {{/* Use file storage to store log read checkpoints. */}}
    storage: file_storage/log_checkpoints
    include_file_path: true
    include_file_name: false
    operators:
      # Find out which format is used by kubernetes
      - type: router
        id: get-format
        routes:
          - output: parser-docker
            expr: 'body matches "^\\{"'
          - output: parser-crio
            expr: 'body matches "^[^ Z]+ "'
          - output: parser-containerd
            expr: 'body matches "^[^ Z]+Z"'
      # Parse CRI-O format
      - type: regex_parser
        id: parser-crio
        regex: '^(?P<time>[^ Z]+) (?P<stream>stdout|stderr) (?P<logtag>[^ ]*) ?(?P<log>.*)$'
        output: extract_metadata_from_filepath
        timestamp:
          parse_from: attributes.time
          layout_type: gotime
          layout: '2006-01-02T15:04:05.999999999-07:00'
      # Parse CRI-Containerd format
      - type: regex_parser
        id: parser-containerd
        regex: '^(?P<time>[^ ^Z]+Z) (?P<stream>stdout|stderr) (?P<logtag>[^ ]*) ?(?P<log>.*)$'
        output: extract_metadata_from_filepath
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'
      # Parse Docker format
      - type: json_parser
        id: parser-docker
        output: extract_metadata_from_filepath
        timestamp:
          parse_from: attributes.time
          layout: '%Y-%m-%dT%H:%M:%S.%LZ'
      # Extract metadata from file path
      - id: extract_metadata_from_filepath
        type: regex_parser
        regex: ^.*\/(?P<k8s_namespace_name>[^_]+)_(?P<k8s_pod_name>[^_]+)_(?P<k8s_pod_uid>[a-f0-9\-]+)\/(?P<k8s_container_name>[^\._]+)\/(?P<k8s_container_restart_count>\d+)\.log$
        parse_from: attributes["log.file.path"]
      # Copy renamed attributes
      - type: copy
        from: attributes.stream
        to: attributes["log.iostream"]
      - type: copy
        from: attributes.k8s_container_name
        to: resource["k8s.container.name"]
      - type: copy
        from: attributes.k8s_namespace_name
        to: resource["k8s.namespace.name"]
      - type: copy
        from: attributes.k8s_pod_name
        to: resource["k8s.pod.name"]
      - type: copy
        from: attributes.k8s_pod_uid
        to: resource["k8s.pod.uid"]
      # Clean up log body
      - type: move
        from: attributes.log
        to: body
      # Remove field not needed anymore.
      - type: remove
        field: attributes.k8s_container_restart_count
{{- end }}

{{- define "opentelemetry-collector.applyKubernetesAttributesConfig" -}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.kubernetesAttributesConfig" .Values | fromYaml) .config }}
{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.kubernetesAttributesConfig" -}}
processors:
  k8sattributes:
    auth_type: serviceAccount
    passthrough: false
    filter:
      node_from_env_var: K8S_NODE_NAME
    extract:
      metadata:
        - k8s.pod.name
        - k8s.deployment.name
        - k8s.cluster.uid
        - k8s.namespace.name
        - k8s.node.name
    pod_association:
    - sources:
      - from: resource_attribute
        name: k8s.pod.name
{{- end }}

{{- define "opentelemetry-collector.applyGrafanaStackConfig" -}}
{{/* Merge overwrite Grafana stack exporters config into full config */}}
{{- $config := mustMergeOverwrite (include "opentelemetry-collector.grafanaStackExportersConfig" .Values | fromYaml) .config }}

{{/* Merge Tempo pipeline config into existing pipelines config */}}
{{- $tempoPipelineConfig := (include "opentelemetry-collector.grafanaStackTempoPipelineConfig" . | fromYaml) }}
{{- $_ := set (index $config "service") "pipelines" (mustMergeOverwrite (index $config "service" "pipelines") (index $tempoPipelineConfig "pipelines")) }}

{{/* Merge Loki pipeline config into existing pipelines config */}}
{{- $lokiPipelineConfig := (include "opentelemetry-collector.grafanaStackLokiPipelineConfig" . | fromYaml) }}
{{- $_ := set (index $config "service") "pipelines" (mustMergeOverwrite (index $config "service" "pipelines") (index $lokiPipelineConfig "pipelines")) }}

{{/* Append prometheusremotewrite to metrics/geti exporters */}}
{{- $_ := set (index $config "service" "pipelines" "metrics/geti" ) "exporters" (append (index $config "service" "pipelines" "metrics/geti" "exporters") "prometheusremotewrite" | uniq)  }}
{{/* Append prometheusremotewrite to metrics/k8s exporters */}}
{{- $_ := set (index $config "service" "pipelines" "metrics/k8s" ) "exporters" (append (index $config "service" "pipelines" "metrics/k8s" "exporters") "prometheusremotewrite" | uniq)  }}

{{- $config | toYaml }}
{{- end }}

{{- define "opentelemetry-collector.grafanaStackExportersConfig" -}}
exporters:
    loki:
      endpoint: http://loki:3100/loki/api/v1/push
      timeout: 10s
    prometheusremotewrite:
      endpoint: "http://{{ .Release.Namespace }}-mimir:9009/api/v1/push"
      remote_write_queue:
        enabled: true
        queue_size: 20000
        num_consumers: 10
      timeout: 30s
      tls:
        insecure: true
      resource_to_telemetry_conversion:
        enabled: true
    otlp/traces:
      endpoint: "{{ .Release.Namespace }}-tempo.{{ .Release.Namespace }}:4317"
      tls:
        insecure: true
{{- end }}

{{- define "opentelemetry-collector.grafanaStackTempoPipelineConfig" -}}
pipelines:
  traces/geti/tempo:
    exporters:
      - otlp/traces
    processors:
      - memory_limiter
      - k8sattributes
      - batch/traces_geti
      - filter/traces
      - redaction/traces_email
    receivers:
      - otlp
{{- end }}

{{- define "opentelemetry-collector.grafanaStackLokiPipelineConfig" -}}
pipelines:
  logs/geti/loki:
    exporters:
      - loki
    processors:
      - memory_limiter
      - k8sattributes
      - batch/logs_geti
      - resource/logs
      - attributes/logs
      - transform/logs_emails
    receivers:
      - otlp
      - filelog
  logs/k8s/loki:
    exporters:
      - loki
    processors:
      - memory_limiter
      - k8sattributes
      - batch/logs_k8s
      - attributes/logs
      - transform/logs_emails
    receivers:
      - k8s_events
{{- end }}

{{/* Build the list of port for deployment service */}}
{{- define "opentelemetry-collector.deploymentPortsConfig" -}}
{{- $ports := deepCopy .Values.ports }}
{{- range $key, $port := $ports }}
{{- if $port.enabled }}
- name: {{ $key }}
  port: {{ $port.servicePort }}
  targetPort: {{ $port.servicePort }}
  protocol: {{ $port.protocol }}
{{- end }}
{{- end }}
{{- end }}

