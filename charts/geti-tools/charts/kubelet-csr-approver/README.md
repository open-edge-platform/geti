# kubelet-csr-approver

Kubelet CSR approver is a Kubernetes controller whose sole purpose is to
auto-approve [`kubelet-serving` Certificate Signing Request
(CSR)](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/#kubelet-serving-certs),
provided these CSRs comply with a series of configurable, provider-specific,
checks/verifications.

Kubelet CSR approver is being kept up-to-date in accordance with the [most
recent three Kubernetes minor releases](https://kubernetes.io/releases/).

## Helm Install

Adjust `providerRegex`, `providerIpPrefixes` and `maxExpirationSeconds` as needed.

```bash
helm repo add kubelet-csr-approver https://postfinance.github.io/kubelet-csr-approver
helm install kubelet-csr-approver kubelet-csr-approver/kubelet-csr-approver -n kube-system \
  --set providerRegex='^node-\w*\.int\.company\.ch$' \
  --set providerIpPrefixes='192.168.8.0/22' \
  --set maxExpirationSeconds='86400'
  --set bypassDnsResolution='false'
```

### Parameters

The most important parameters (configurable through either flags or environment
variables) are:

* `--provider-regex` or `PROVIDER_REGEX` lets you decide which hostnames can be
approved or not\
e.g. if all your nodes follow a naming convention (say
`node-randomstr1234.int.company.ch`), your regex could look like
`^node-\w*\.int\.company\.ch$`
* `--max-expiration-sec` or `MAX_EXPIRATION_SEC` lets you specify the maximum
`expirationSeconds` the kubelet can ask for.\
Per default it is hardcoded to a maximum of 367 days, and can be reduced with
this parameter.
* `--bypass-dns-resolution` or `BYPASS_DNS_RESOLUTION` -> permits to bypass DNS resolution
check. \
the default value of the boolean is false, and you can enable it by
setting it to `true` (or any other option listed in GoLang's
[`ParseBool`](https://github.com/golang/go/blob/master/src/strconv/atob.go#L10)
function)
* `--bypass-hostname-check` or `BYPASS_HOSTNAME_CHECK`: when set to true,
it permits having a DNS name that differs (i.e. isn't prefixed) by the hostname
* `--provider-ip-prefixes`  or `PROVIDER_IP_PREFIXES` permits to specify a
  comma-separated list of IP (v4 or/and v6) subnets/prefixes, that CSR IP
  addresses shall fall into. left unspecified, all IP addresses are allowed. \
  you can for example set it to `192.168.0.0/16,fc00::/7` if this reflects your
  local network IP ranges.
* `--ignore-non-system-node` or `IGNORE_NON_SYSTEM_NODE` permits ignoring CSRs
  with a _Username_ different than `system:node:......`. \
  the default value of the boolean is false, and if you want to use this feature
  you need to set this flag to `true`
* `--allowed-dns-names` or `ALLOWED_DNS_NAMES` permits allowing more than one
  DNS name in the certificate request. the default value is set to 1.
* `--leader-election` or `LEADER_ELECTION` permits enabling leader election
  when running with multiple replicas

It is important to understand that the node DNS name needs to be
resolvable for the `kubelet-csr-approver` to work properly. If this is an issue
for you, please file an issue and I'll add a flag to disable this validation.

ℹ have a look below in this README to understand which other validation
mechanisms are put in place.

More information can be found on the [projet's homepage](https://github.com/postfinance/kubelet-csr-approver)
