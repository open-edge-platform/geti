{{- define "opentelemetry-collector.pod" -}}
serviceAccountName: {{ include "opentelemetry-collector.serviceAccountName" . }}
securityContext:
  {{- toYaml .Values.podSecurityContext | nindent 2 }}
containers:
  - name: {{ .Chart.Name }}
    command:
      - /{{ .Values.command.name }}
      {{- if .Values.configMap.create }}
      - --config=/conf/relay.yaml
      {{- end }}
      {{- range .Values.command.extraArgs }}
      - {{ . }}
      {{- end }}
    securityContext:
      {{- toYaml .Values.securityContext | nindent 6 }}
    image: {{ .Values.image.registry }}/{{ .Values.image.repository }}/{{ .Values.image.name }}
    imagePullPolicy: {{ .Values.image.pullPolicy }}
    ports:
      {{- range $key, $port := .Values.ports }}
      {{- if $port.enabled }}
      - name: {{ $key }}
        containerPort: {{ $port.containerPort }}
        protocol: {{ $port.protocol }}
        {{- if and $.isAgent $port.hostPort }}
        hostPort: {{ $port.hostPort }}
        {{- end }}
      {{- end }}
      {{- end }}
    env:
      {{- if .Values.presets.hostMetrics.enabled }}
      - name: HOST_PROC
        value: /hostfs/proc
      - name: HOST_SYS
        value: /hostfs/sys
      - name: HOST_ETC
        value: /hostfs/etc
      - name: HOST_VAR
        value: /hostfs/var
      - name: HOST_RUN
        value: /hostfs/run
      - name: HOST_DEV
        value: /hostfs/dev
      {{- end }}
      {{- if .Values.presets.kubeletMetrics.enabled }}
      - name: K8S_NODE_NAME
        valueFrom:
          fieldRef:
            apiVersion: v1
            fieldPath: spec.nodeName
      - name: K8S_POD_IP
        valueFrom:
          fieldRef:
            apiVersion: v1
            fieldPath: status.podIP
      {{- end }}
      {{- with .Values.extraEnvs }}
      {{- . | toYaml | nindent 6 }}
      {{- end }}
    {{- if .Values.lifecycleHooks }}
    lifecycle:
      {{- toYaml .Values.lifecycleHooks | nindent 6 }}
    {{- end }}
    livenessProbe:
      httpGet:
        path: /
        port: 13133
    readinessProbe:
      httpGet:
        path: /
        port: 13133
    resources:
      {{- toYaml .Values.resources | nindent 6 }}
    volumeMounts:
      {{- if .Values.configMap.create }}
      - mountPath: /conf
        name: {{ .Chart.Name }}-configmap
      {{- end }}
      {{- range .Values.extraConfigMapMounts }}
      - name: {{ .name }}
        mountPath: {{ .mountPath }}
        readOnly: {{ .readOnly }}
        {{- if .subPath }}
        subPath: {{ .subPath }}
        {{- end }}
      {{- end }}
      {{- range .Values.extraHostPathMounts }}
      - name: {{ .name }}
        mountPath: {{ .mountPath }}
        readOnly: {{ .readOnly }}
        {{- if .mountPropagation }}
        mountPropagation: {{ .mountPropagation }}
        {{- end }}
      {{- end }}
      {{- range .Values.secretMounts }}
      - name: {{ .name }}
        mountPath: {{ .mountPath }}
        readOnly: {{ .readOnly }}
        {{- if .subPath }}
        subPath: {{ .subPath }}
        {{- end }}
      {{- end }}
      {{- if eq (include "opentelemetry-collector.logsCollectionEnabled" .) "true" }}
      - name: varlogpods
        mountPath: /var/log/pods
        readOnly: true
      - name: varlibdockercontainers
        mountPath: /var/lib/docker/containers
        readOnly: true
      {{- end }}
      {{- if .Values.presets.hostMetrics.enabled }}
      - name: hostfs
        mountPath: /hostfs
        readOnly: true
        mountPropagation: HostToContainer
      {{- end }}
      {{- if .Values.extraVolumeMounts }}
      {{- toYaml .Values.extraVolumeMounts | nindent 6 }}
      {{- end }}
{{- if .Values.initContainers }}
initContainers:
  {{- range .Values.initContainers }}
  - name: {{ .name }}
    command: 
      {{- .command | toYaml | nindent 8 }}
    image: "{{ .image.registry }}/{{ .image.repository }}/{{ .image.name }}"
    resources:
      requests:
        cpu: {{ .resources.requests.cpu }}
        memory: {{ .resources.requests.memory }}
      limits:
        cpu: {{ .resources.limits.cpu }}
        memory: {{ .resources.limits.memory }}
    volumeMounts:
      {{- range .volumeMounts }}
      - mountPath: {{ .mountPath }}
        name: {{ .name }}
        subPath: {{ .subPath | default "" }}
        readOnly: {{ .readOnly | default false }}
      {{- end }}
    securityContext:
      readOnlyRootFilesystem: {{ .securityContext.readOnlyRootFilesystem | default false }}
      allowPrivilegeEscalation: {{ .securityContext.allowPrivilegeEscalation | default false }}
  {{- end }}
{{- end }}
{{- if .Values.priorityClassName }}
priorityClassName: {{ .Values.priorityClassName | quote }}
{{- end }}
volumes:
  {{- if .Values.configMap.create }}
  - name: {{ .Chart.Name }}-configmap
    configMap:
      name: {{ include "opentelemetry-collector.fullname" . }}{{ .configmapSuffix }}
      items:
        - key: relay
          path: relay.yaml
  {{- end }}
  {{- range .Values.extraConfigMapMounts }}
  - name: {{ .name }}
    configMap:
      name: {{ .configMap }}
  {{- end }}
  {{- range .Values.extraHostPathMounts }}
  - name: {{ .name }}
    hostPath:
      path: {{ .hostPath }}
  {{- end }}
  {{- range .Values.secretMounts }}
  - name: {{ .name }}
    secret:
      secretName: {{ .secretName }}
  {{- end }}
  {{- if eq (include "opentelemetry-collector.logsCollectionEnabled" .) "true" }}
  - name: varlogpods
    hostPath:
      path: /var/log/pods
  - name: varlibdockercontainers
    hostPath:
      path: /var/lib/docker/containers
  {{- end }}
  {{- if .Values.presets.hostMetrics.enabled }}
  - name: hostfs
    hostPath:
      path: /
  {{- end }}
  {{- if .Values.extraVolumes }}
  {{- toYaml .Values.extraVolumes | nindent 2 }}
  {{- end }}
{{- with .Values.nodeSelector }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.affinity }}
affinity:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- with .Values.tolerations }}
tolerations:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
