{{/*
Common labels applied to all resources.
*/}}
{{- define "app.labels" -}}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: fastapi-oidc-platform
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels for a specific component.
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .root.Release.Name }}
{{- end }}

{{/*
Construct full image reference with optional registry prefix.
*/}}
{{- define "app.image" -}}
{{- if .root.Values.global.imageRegistry -}}
{{ .root.Values.global.imageRegistry }}/{{ .image.repository }}:{{ .image.tag | default "latest" }}
{{- else -}}
{{ .image.repository }}:{{ .image.tag | default "latest" }}
{{- end -}}
{{- end }}

{{/*
Standard security context for all containers (OWASP A05).
Non-root, read-only root filesystem, drop all capabilities.
*/}}
{{- define "app.securityContext" -}}
runAsNonRoot: true
runAsUser: 1001
runAsGroup: 1001
fsGroup: 1001
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{- define "app.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
runAsNonRoot: true
runAsUser: 1001
capabilities:
  drop:
    - ALL
{{- end }}
