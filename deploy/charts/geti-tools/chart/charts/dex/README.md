# dex

![version: 0.0.6](https://img.shields.io/badge/version-0.0.6-informational?style=flat-square) ![type: application](https://img.shields.io/badge/type-application-informational?style=flat-square) ![app version: 2.28.0](https://img.shields.io/badge/app%20version-2.28.0-informational?style=flat-square) ![kube version: >=1.14.0-0](https://img.shields.io/badge/kube%20version->=1.14.0--0-informational?style=flat-square) [![artifact hub](https://img.shields.io/badge/artifact%20hub-dex-informational?style=flat-square)](https://artifacthub.io/packages/helm/dex/dex)

OpenID Connect (OIDC) identity and OAuth 2.0 provider with pluggable connectors

**Homepage:** <https://dexidp.io/>

## TL;DR;

```bash
helm repo add dex https://charts.dexidp.io
helm install --generate-name --wait dex/dex
```

## Getting started

### Minimal configuration

Dex requires a minimal configuration in order to work.
You can pass configuration to Dex using Helm values:

```yaml
config:
  # Set it to a valid URL
  issuer: http://my-issuer-url.com

  # See https://dexidp.io/docs/storage/ for more options
  storage:
    type: memory

  # Enable at least one connector
  # See https://dexidp.io/docs/connectors/ for more options
  enablePasswordDB: true
```

The above configuration won't make Dex automatically available on the configured URL.
One (and probably the easiest) way to achieve that is configuring an ingress:

```yaml
ingress:
  enabled: true

  hosts:
    - host: my-issuer-url.com
      paths:
        - path: /
```

### Minimal TLS configuration

HTTPS is basically mandatory these days, especially for authentication and authorization services.
There are several solutions for protecting services with TLS in Kubernetes,
but by far the most popular and portable is undoubtedly [Cert Manager](https://cert-manager.io).

Cert Manager can be [installed](https://cert-manager.io/docs/installation/kubernetes) with a few steps:

```shell
helm repo add jetstack https://charts.jetstack.io
helm repo update
kubectl create namespace cert-manager
helm install \
  cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --set installCRDs=true
```

The next step is setting up an [issuer](https://cert-manager.io/docs/concepts/issuer/) (eg. [Let's Encrypt](https://letsencrypt.org/)):

```shell
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: acme
spec:
  acme:
    email: YOUR@EMAIL_ADDRESS
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: acme-account-key
    solvers:
    - http01:
       ingress:
         class: YOUR_INGRESS_CLASS
EOF
```

Finally, change the ingress config to use TLS:

```yaml
ingress:
  enabled: true

  annotations:
    cert-manager.io/cluster-issuer: acme

  hosts:
    - host: my-issuer-url.com
      paths:
        - path: /

  tls:
    - hosts:
        - my-issuer-url.com
      secretName: dex-cert
```

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| replicaCount | int | `1` | Number of Pods to launch. |
| image.repository | string | `"ghcr.io/dexidp/dex"` | Repository to pull the container image from. |
| image.pullPolicy | string | `"IfNotPresent"` | Image [pull policy](https://kubernetes.io/docs/concepts/containers/images/#updating-images) |
| image.tag | string | `""` | Overrides the image tag (default is the chart appVersion). |
| imagePullSecrets | list | `[]` | Image [pull secrets](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#create-a-pod-that-uses-your-secret) |
| nameOverride | string | `""` | Provide a name in place of the chart name for `app:` labels. |
| fullnameOverride | string | `""` | Provide a name to substitute for the full names of resources. |
| https.enabled | bool | `false` | Enable the HTTPS endpoint. |
| grpc.enabled | bool | `false` | Enable the gRPC endpoint. Read more in the [documentation](https://dexidp.io/docs/api/). |
| config | object | `{}` | Application configuration. See the [official documentation](https://dexidp.io/docs/). |
| volumes | list | `[]` | Additional storage [volumes](https://kubernetes.io/docs/concepts/storage/volumes/) of a Pod. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/pod-v1/#volumes) for details. |
| volumeMounts | list | `[]` | Additional [volume mounts](https://kubernetes.io/docs/tasks/configure-pod-container/configure-volume-storage/) of a container. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/container/#volumes) for details. |
| envFrom | list | `[]` | Configure a [Secret](https://kubernetes.io/docs/concepts/configuration/secret/#using-secrets-as-environment-variables) or a [ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/#configure-all-key-value-pairs-in-a-configmap-as-container-environment-variables) as environment variable sources for a Pod. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/container/#environment-variables) for details. |
| env | object | `{}` | Pass environment variables directly to a Pod. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/container/#environment-variables) for details. |
| serviceAccount.create | bool | `true` | Whether a service account should be created. |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account. |
| serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template. |
| rbac.create | bool | `true` | Specifies whether RBAC resources should be created. If disabled, the operator is responsible for creating the necessary resources based on the templates. |
| podAnnotations | object | `{}` | Custom annotations for a Pod. |
| podSecurityContext | object | `{}` | Pod [security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-the-security-context-for-a-pod). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/pod-v1/#security-context) for details. |
| securityContext | object | `{}` | Container [security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/#set-the-security-context-for-a-container). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/container/#security-context) for details. |
| service.annotations | object | `{}` | Annotations to add to the Service. |
| service.type | string | `"ClusterIP"` | Kubernetes [service type](https://kubernetes.io/docs/concepts/services-networking/service/#publishing-services-service-types). |
| service.ports.http.port | int | `5556` | HTTP service port |
| service.ports.http.nodePort | int | `nil` | HTTP node port (when applicable) |
| service.ports.grpc.port | int | `5557` | gRPC service port |
| service.ports.grpc.nodePort | int | `nil` | gRPC node port (when applicable) |
| ingress | object | Disabled by default. | Ingress configuration (see [values.yaml](values.yaml) for details). |
| resources | object | No requests or limits. | Container resource [requests and limits](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/). See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/container/#resources) for details. |
| autoscaling | object | Disabled by default. | Autoscaling configuration (see [values.yaml](values.yaml) for details). |
| nodeSelector | object | `{}` | [Node selector](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#nodeselector) configuration. |
| tolerations | list | `[]` | [Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/) for node taints. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/pod-v1/#scheduling) for details. |
| affinity | object | `{}` | [Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity) configuration. See the [API reference](https://kubernetes.io/docs/reference/kubernetes-api/workloads-resources/pod-v1/#scheduling) for details. |

## Migrating from stable/dex (or banzaicloud-stable/dex) chart

This chart is not backwards compatible with the `stable/dex` (or `banzaicloud-stable/dex`) chart.

However, Dex itself remains backwards compatible, so you can easily install the new chart in place of the old one
and continue using Dex with a minimal downtime.
