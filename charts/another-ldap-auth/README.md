# another-ldap-auth

![Version: 1.0.1](https://img.shields.io/badge/Version-1.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 3.1.1](https://img.shields.io/badge/AppVersion-3.1.1-informational?style=flat-square)

Helm chart using docker.io/jgkirschbaum/another-ldap-auth to enable AD or LDAP based basic-authentication for ingress resources

**Homepage:** <https://github.com/jgkirschbaum/another-ldap-auth>

## Source Code

* <https://github.com/jgkirschbaum/another-ldap-auth>

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| affinity | object | `{}` | Special node affinity settings |
| autoscaling | object | *See values defined below* | Definitions for the [Horizontal Pod Autoscaler (HPA)](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/), usually not needed. First try setting `numberOfWorkers` |
| autoscaling.enabled | bool | `false` | Wether the hpa is enabled or not |
| autoscaling.maxReplicas | int | `100` | Maximim number of replicas |
| autoscaling.minReplicas | int | `1` | How many replicas shout at least exist |
| autoscaling.targetCPUUtilizationPercentage | int | `80` | When should new replicas be started depending on cpu utilization |
| autoscaling.targetMemoryUtilizationPercentage | string | `""` | When should new replicas be started depending on memory utilization |
| fullnameOverride | string | `""` | String to fully override rabbitmq.fullname template |
| image.pullPolicy | string | `"IfNotPresent"` | Image pull policy |
| image.repository | string | `"jgkirschbaum/another-ldap-auth"` | Path to the image |
| image.tag | string | `"3.1.0"` | Image tag to use |
| imagePullSecrets | list | `[]` | Specify docker-registry secret names as an array |
| ldap.bindDN | string | `"{username}@TESTMYLDAP.com"` | Depends on your LDAP server the binding structure can change. This field supports variable expansion for the username. |
| ldap.cacheExpiration | int | `5` | Cache expiration in minutes |
| ldap.endpoint | string | `"ldaps://testmyldap.com:636"` | LDAP endpoint |
| ldap.existingSecret | string | `""` | Use an existing secret for the `managerDnUsername` password |
| ldap.managerDnPassword | string | `nil` | Passwort for `managerDnUsername`, only used when `existingSecret` is not set |
| ldap.managerDnUsername | string | `"CN=john,OU=Administrators,DC=TESTMYLDAP,DC=COM"` | Username for LDAP bind requests |
| ldap.searchBase | string | `"DC=TESTMYLDAP,DC=COM"` | Base in directory tree where the search starts |
| ldap.searchFilter | string | `"(sAMAccountName={username})"` | Filter for search, for Microsoft Active Directory usually you can use `sAMAccountName` |
| nameOverride | string | `""` | String to partially override rabbitmq.fullname template (will maintain the release name) |
| nodeSelector | object | `{}` | Special node selector settings |
| podAnnotations | object | `{}` | Special annotations for the pod |
| podSecurityContext | object | `{}` | Special security context for the pod |
| replicaCount | int | `1` | should not be changed, due to caching is done on a per pod basis. Only use it in very heavy loaded environments |
| resources | object | `{}` | Resource requests and limits |
| securityContext | object | `{}` | Special security context for the container |
| server.TlsCaCert | string | `""` | Server ca certificates |
| server.TlsCert | string | `""` | Server certificate |
| server.TlsEnabled | bool | `false` | Enable TLS for the pod. If `useWsgiServer` is `true` you also need the `TlsKey` and `TlsCert`.  If `useWsgiServer` is `false` you need not to specify `TlsKey` and `TlsCert` and use the on the fly generated key and certificate |
| server.TlsKey | string | `""` | Server private key |
| server.logFormat | string | `"TEXT"` | Logformat of the server: `TEXT` or `JSON` |
| server.logLevel | string | `"INFO"` | Loglevel of the server: `INFO`, `WARNING`, `ERROR`, `DEBUG` |
| server.numberOfWorkers | int | `1` | Number of worker processes for the [Gunicorn](https://gunicorn.org/) WSGI Server Should not be changed, due to caching is done on a per process basis Only use it in very heavy loaded environments |
| server.useWsgiServer | bool | `true` | Enables or disables the [Gunicorn](https://gunicorn.org/) WSGI Server |
| service.containerPort | int | `9000` | Port of the container to connect |
| service.port | int | `80` | Port of the service |
| service.protocol | string | `"TCP"` | Protocol of the service |
| service.type | string | `"ClusterIP"` | Type of the service |
| serviceAccount.annotations | object | `{}` | Annotations to add to the service account |
| serviceAccount.create | bool | `true` | Specifies whether a service account should be created |
| serviceAccount.name | string | `""` | The name of the service account to use. If not set and create is true, a name is generated using the fullname template |
| tolerations | list | `[]` | Special tolerations settings |
| topologySpreadConstraints | list | `[]` | Special topology settings |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.11.3](https://github.com/norwoodj/helm-docs/releases/v1.11.3)
