{{- define "edd-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "edd-platform.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "edd-platform.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/name: {{ include "edd-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "edd-platform.baseSelectorLabels" -}}
app.kubernetes.io/name: {{ include "edd-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "edd-platform.selectorLabels" -}}
{{- include "edd-platform.baseSelectorLabels" . }}
app.kubernetes.io/component: service
{{- end -}}

{{- define "edd-platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- include "edd-platform.fullname" . -}}
{{- else -}}
default
{{- end -}}
{{- end -}}

{{- define "edd-platform.secretName" -}}
{{- if .Values.secrets.existingSecretName -}}
{{- .Values.secrets.existingSecretName -}}
{{- else -}}
{{- printf "%s-secrets" (include "edd-platform.fullname" .) -}}
{{- end -}}
{{- end -}}

{{- define "edd-platform.postgresName" -}}
{{- printf "%s-postgres" (include "edd-platform.fullname" .) -}}
{{- end -}}

{{- define "edd-platform.consoleName" -}}
{{- printf "%s-console" (include "edd-platform.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "edd-platform.consoleSelectorLabels" -}}
app.kubernetes.io/name: {{ include "edd-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: console
{{- end -}}

{{- define "edd-platform.workerName" -}}
{{- printf "%s-worker" (include "edd-platform.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "edd-platform.workerSelectorLabels" -}}
app.kubernetes.io/name: {{ include "edd-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: worker
{{- end -}}

{{- define "edd-platform.serviceUrl" -}}
{{- printf "http://%s:%d" (include "edd-platform.fullname" .) (.Values.service.port | int) -}}
{{- end -}}
