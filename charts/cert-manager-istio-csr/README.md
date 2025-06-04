# istio-csr

<!-- see https://artifacthub.io/packages/helm/cert-manager/cert-manager-istio-csr for the rendered version -->

## Helm Values

<!-- AUTO-GENERATED -->

#### **nameOverride** ~ `string`

nameOverride replaces the name of the chart in the Chart.yaml file, when this is used to construct Kubernetes object names.

#### **replicaCount** ~ `number`
> Default value:
> ```yaml
> 1
> ```

Number of replicas of istio-csr to run.
#### **image.registry** ~ `string`

Target image registry. This value is prepended to the target image repository, if set.  
For example:

```yaml
registry: quay.io
repository: jetstack/cert-manager-istio-csr
```

#### **image.repository** ~ `string`
> Default value:
> ```yaml
> quay.io/jetstack/cert-manager-istio-csr
> ```

Target image repository.
#### **image.tag** ~ `string`

Override the image tag to deploy by setting this variable. If no value is set, the chart's appVersion is used.

#### **image.digest** ~ `string`

Target image digest. Override any tag, if set.  
For example:

```yaml
digest: sha256:0e072dddd1f7f8fc8909a2ca6f65e76c5f0d2fcfb8be47935ae3457e8bbceb20
```

#### **image.pullPolicy** ~ `string`
> Default value:
> ```yaml
> IfNotPresent
> ```

Kubernetes imagePullPolicy on Deployment.
#### **imagePullSecrets** ~ `array`
> Default value:
> ```yaml
> []
> ```

Optional secrets used for pulling the istio-csr container image.
#### **service.type** ~ `string`
> Default value:
> ```yaml
> ClusterIP
> ```

Service type to expose istio-csr gRPC service.
#### **service.port** ~ `number`
> Default value:
> ```yaml
> 443
> ```

Service port to expose istio-csr gRPC service.
#### **service.nodePort** ~ `number`

Service nodePort to expose istio-csr gRPC service.


#### **app.logLevel** ~ `number`
> Default value:
> ```yaml
> 1
> ```

Verbosity of istio-csr logging.
#### **app.logFormat** ~ `string`
> Default value:
> ```yaml
> text
> ```

Output format of istio-csr logging.
#### **app.metrics.port** ~ `number`
> Default value:
> ```yaml
> 9402
> ```

Port for exposing Prometheus metrics on 0.0.0.0 on path '/metrics'.
#### **app.metrics.service.enabled** ~ `bool`
> Default value:
> ```yaml
> true
> ```

Create a Service resource to expose metrics endpoint.
#### **app.metrics.service.type** ~ `string`
> Default value:
> ```yaml
> ClusterIP
> ```

Service type to expose metrics.
#### **app.metrics.service.servicemonitor.enabled** ~ `bool`
> Default value:
> ```yaml
> false
> ```

Create Prometheus ServiceMonitor resource for approver-policy.
#### **app.metrics.service.servicemonitor.prometheusInstance** ~ `string`
> Default value:
> ```yaml
> default
> ```

The value for the "prometheus" label on the ServiceMonitor. This allows for multiple Prometheus instances selecting difference ServiceMonitors using label selectors.
#### **app.metrics.service.servicemonitor.interval** ~ `string`
> Default value:
> ```yaml
> 10s
> ```

The interval that the Prometheus will scrape for metrics.
#### **app.metrics.service.servicemonitor.scrapeTimeout** ~ `string`
> Default value:
> ```yaml
> 5s
> ```

The timeout on each metric probe request.
#### **app.metrics.service.servicemonitor.labels** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Additional labels to give the ServiceMonitor resource.
#### **app.runtimeConfiguration.create** ~ `bool`
> Default value:
> ```yaml
> false
> ```

Create the runtime-configuration ConfigMap
#### **app.runtimeConfiguration.name** ~ `string`
> Default value:
> ```yaml
> ""
> ```

Name of a ConfigMap in the installation namespace to watch, providing runtime configuration of an issuer to use.  
  
If create is set to true then this name is used to create the ConfigMap, otherwise the ConfigMap must exist and the "issuer-name", "issuer-kind" and "issuer-group" keys must be present in it.
#### **app.runtimeConfiguration.issuer.name** ~ `string`
> Default value:
> ```yaml
> istio-ca
> ```

Issuer name set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.runtimeConfiguration.issuer.kind** ~ `string`
> Default value:
> ```yaml
> Issuer
> ```

Issuer kind set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.runtimeConfiguration.issuer.group** ~ `string`
> Default value:
> ```yaml
> cert-manager.io
> ```

Issuer group name set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.readinessProbe.port** ~ `number`
> Default value:
> ```yaml
> 6060
> ```

Container port to expose istio-csr HTTP readiness probe on default network interface.
#### **app.readinessProbe.path** ~ `string`
> Default value:
> ```yaml
> /readyz
> ```

Path to expose istio-csr HTTP readiness probe on default network interface.
#### **app.certmanager.namespace** ~ `string`
> Default value:
> ```yaml
> istio-system
> ```

Namespace to create CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.certmanager.preserveCertificateRequests** ~ `bool`
> Default value:
> ```yaml
> false
> ```

Don't delete created CertificateRequests once they have been signed. WARNING: do not enable this option in production, or environments with any non-trivial number of workloads for an extended period of time. Doing so will balloon the resource consumption of both ETCD and the API server, leading to errors and slow down. This option is intended for debugging purposes only, for limited periods of time.
#### **app.certmanager.additionalAnnotations** ~ `array`
> Default value:
> ```yaml
> []
> ```

Additional annotations to include on certificate requests.  
Takes key/value pairs in the format:

```yaml
additionalAnnotations:
  - name: custom.cert-manager.io/policy-name
    value: istio-csr
```
#### **app.certmanager.issuer.enabled** ~ `bool`
> Default value:
> ```yaml
> true
> ```

Enable the default issuer, this is the issuer used when no runtime configuration is provided.  
  
When enabled the istio-csr Pod will not be "Ready" until the issuer has been used to issue the istio-csr GRPC certificate.  
  
For istio-csr to function either this or runtime configuration must be enabled.
#### **app.certmanager.issuer.name** ~ `string`
> Default value:
> ```yaml
> istio-ca
> ```

Issuer name set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.certmanager.issuer.kind** ~ `string`
> Default value:
> ```yaml
> Issuer
> ```

Issuer kind set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.certmanager.issuer.group** ~ `string`
> Default value:
> ```yaml
> cert-manager.io
> ```

Issuer group name set on created CertificateRequests for both istio-csr's serving certificate and incoming gRPC CSRs.
#### **app.tls.trustDomain** ~ `string`
> Default value:
> ```yaml
> cluster.local
> ```

The Istio cluster's trust domain.
#### **app.tls.rootCAFile** ~ `unknown`
> Default value:
> ```yaml
> null
> ```

An optional file location to a PEM encoded root CA that the root CA. ConfigMap in all namespaces will be populated with. If empty, the CA returned from cert-manager for the serving certificate will be used.
#### **app.tls.certificateDNSNames[0]** ~ `string`
> Default value:
> ```yaml
> cert-manager-istio-csr.cert-manager.svc
> ```
#### **app.tls.certificateDuration** ~ `string`
> Default value:
> ```yaml
> 1h
> ```

Requested duration of gRPC serving certificate. Will be automatically renewed.  
Based on NIST 800-204A recommendations (SM-DR13).  
https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204A.pdf
#### **app.tls.istiodCertificateEnable** ~ `boolean,string,null`
> Default value:
> ```yaml
> true
> ```

If true, create the istiod certificate using a cert-manager certificate as part of the install. If set to "dynamic", will create the cert dynamically when istio-csr pods start up. If false, no cert is created.

#### **app.tls.istiodCertificateDuration** ~ `string`
> Default value:
> ```yaml
> 1h
> ```

Requested duration of istio's Certificate. Will be automatically renewed. Default is based on NIST 800-204A recommendations (SM-DR13). https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204A.pdf. Warning: cert-manager does not allow a duration on Certificates less than 1 hour.
#### **app.tls.istiodCertificateRenewBefore** ~ `string`
> Default value:
> ```yaml
> 30m
> ```

Amount of time to wait before trying to renew the istiod certificate.  
Must be smaller than the certificate's duration.
#### **app.tls.istiodPrivateKeyAlgorithm** ~ `string`
> Default value:
> ```yaml
> ""
> ```

Private key algorithm to use. For backwards compatibility, defaults to the same value as app.server.serving.signatureAlgorithm
#### **app.tls.istiodPrivateKeySize** ~ `number`
> Default value:
> ```yaml
> 2048
> ```

Parameter for istiod certificate key. For RSA, must be a number of bits >= 2048. For ECDSA, can only be 256 or 384, corresponding to P-256 and P-384 respectively.
#### **app.tls.istiodAdditionalDNSNames** ~ `array`
> Default value:
> ```yaml
> []
> ```

Provide additional DNS names to request on the istiod certificate. Useful if istiod should be accessible via multiple DNS names and/or outside of the cluster.
#### **app.server.authenticators.enableClientCert** ~ `bool`
> Default value:
> ```yaml
> false
> ```

Enable the client certificate authenticator. This will allow workloads to use preexisting certificates to authenticate with istio-csr when rotating their certificate.
#### **app.server.clusterID** ~ `string`
> Default value:
> ```yaml
> Kubernetes
> ```

The istio cluster ID to verify incoming CSRs.
#### **app.server.maxCertificateDuration** ~ `string`
> Default value:
> ```yaml
> 1h
> ```

Maximum validity duration that can be requested for a certificate. istio-csr will request a duration of the smaller of this value, and that of the incoming gRPC CSR.  
Based on NIST 800-204A recommendations (SM-DR13).  
https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-204A.pdf
#### **app.server.serving.address** ~ `string`
> Default value:
> ```yaml
> 0.0.0.0
> ```

Container address to serve istio-csr gRPC service.
#### **app.server.serving.port** ~ `number`
> Default value:
> ```yaml
> 6443
> ```

Container port to serve istio-csr gRPC service.
#### **app.server.serving.certificateKeySize** ~ `number`
> Default value:
> ```yaml
> 2048
> ```

Parameter for serving certificate key. For RSA, must be a number of bits >= 2048. For ECDSA, can only be 256 or 384, corresponding to P-256 and P-384 respectively.
#### **app.server.serving.signatureAlgorithm** ~ `string`
> Default value:
> ```yaml
> RSA
> ```

The type of private key to generate for the serving certificate. Only RSA (default) and ECDSA are supported. NB: This variable is named incorrectly; it controls private key algorithm, not signature algorithm.
#### **app.server.caTrustedNodeAccounts** ~ `string`
> Default value:
> ```yaml
> ""
> ```

A comma-separated list of service accounts that are allowed to use node authentication for CSRs, eg. "istio-system/ztunnel"
#### **app.istio.revisions[0]** ~ `string`
> Default value:
> ```yaml
> default
> ```
#### **app.istio.namespace** ~ `string`
> Default value:
> ```yaml
> istio-system
> ```

The namespace where the istio control-plane is running.
#### **app.controller.leaderElectionNamespace** ~ `string`
> Default value:
> ```yaml
> istio-system
> ```
#### **app.controller.configmapNamespaceSelector** ~ `string`

If set, limit where istio-csr creates configmaps with root ca certificates. If unset, configmap created in ALL namespaces.  
Example: maistra.io/member-of=istio-system


#### **app.controller.disableKubernetesClientRateLimiter** ~ `bool`
> Default value:
> ```yaml
> false
> ```

Allows you to disable the default Kubernetes client rate limiter if istio-csr is exceeding the default QPS (5) and Burst (10) limits. For example in large clusters with many Istio workloads, restarting the Pods may cause istio-csr to send bursts Kubernetes API requests that exceed the limits of the default Kubernetes client rate limiter and istio-csr will become slow to issue certificates for your workloads. Only disable client rate limiting if the Kubernetes API server supports  
[API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/),  
to avoid overloading the server.
#### **deploymentLabels** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Optional extra labels for deployment.
#### **deploymentAnnotations** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Optional extra annotations for deployment.
#### **podLabels** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Optional extra labels for pod.
#### **podAnnotations** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Optional extra annotations for pod.
#### **volumes** ~ `array`
> Default value:
> ```yaml
> []
> ```

Optional extra volumes. Useful for mounting custom root CAs  
  
For example:

```yaml
volumes:
- name: root-ca
  secret:
    secretName: root-cert
```
#### **volumeMounts** ~ `array`
> Default value:
> ```yaml
> []
> ```

Optional extra volume mounts. Useful for mounting custom root CAs  
  
For example:

```yaml
volumeMounts:
- name: root-ca
  mountPath: /etc/tls
```
#### **resources** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Kubernetes pod resources  
ref: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/  
  
For example:

```yaml
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi
```
#### **securityContext.allowPrivilegeEscalation** ~ `bool`
> Default value:
> ```yaml
> false
> ```
#### **securityContext.readOnlyRootFilesystem** ~ `bool`
> Default value:
> ```yaml
> true
> ```
#### **securityContext.runAsNonRoot** ~ `bool`
> Default value:
> ```yaml
> true
> ```
#### **securityContext.capabilities.drop[0]** ~ `string`
> Default value:
> ```yaml
> ALL
> ```
#### **affinity** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Expects input structure as per specification https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.11/#affinity-v1-core  
  
For example:

```yaml
affinity:
  nodeAffinity:
   requiredDuringSchedulingIgnoredDuringExecution:
     nodeSelectorTerms:
     - matchExpressions:
       - key: foo.bar.com/role
         operator: In
         values:
         - master
```
#### **tolerations** ~ `array`
> Default value:
> ```yaml
> []
> ```

Expects input structure as per specification https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.11/#toleration-v1-core  
  
For example:

```yaml
tolerations:
- key: foo.bar.com/role
  operator: Equal
  value: master
  effect: NoSchedule
```
#### **topologySpreadConstraints** ~ `array`
> Default value:
> ```yaml
> []
> ```

List of Kubernetes TopologySpreadConstraints. For more information, see [TopologySpreadConstraint v1 core](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#topologyspreadconstraint-v1-core).  
For example:

```yaml
topologySpreadConstraints:
- maxSkew: 2
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: ScheduleAnyway
  labelSelector:
    matchLabels:
      app.kubernetes.io/name: cert-manager-istio-csr
      app.kubernetes.io/instance: istio-csr
```
#### **nodeSelector** ~ `object`
> Default value:
> ```yaml
> kubernetes.io/os: linux
> ```

Kubernetes node selector: node labels for pod assignment.

#### **commonLabels** ~ `object`
> Default value:
> ```yaml
> {}
> ```

Labels to apply to all resources
#### **extraObjects** ~ `array`
> Default value:
> ```yaml
> []
> ```

Create resources alongside installing istio-csr, via Helm values. Can accept an array of YAML-formatted resources. Each array entry can include multiple YAML documents, separated by '---'  
  
For example:

```yaml
extraObjects:
  - |
    apiVersion: v1
    kind: ConfigMap
    metadata:
      name: '{{ template "cert-manager-istio-csr.fullname" . }}-extra-configmap'
```

<!-- /AUTO-GENERATED -->