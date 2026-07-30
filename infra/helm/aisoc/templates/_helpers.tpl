{{/*
Expand the name of the chart.
*/}}
{{- define "aisoc.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "aisoc.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "aisoc.labels" -}}
helm.sh/chart: {{ include "aisoc.chart" . }}
{{ include "aisoc.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "aisoc.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "aisoc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "aisoc.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "aisoc.api.selectorLabels" -}}
{{ include "aisoc.selectorLabels" . }}
app.kubernetes.io/component: api
{{- end }}

{{- define "aisoc.worker.selectorLabels" -}}
{{ include "aisoc.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{- define "aisoc.frontend.selectorLabels" -}}
{{ include "aisoc.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{- define "aisoc.mcp.selectorLabels" -}}
{{ include "aisoc.selectorLabels" . }}
app.kubernetes.io/component: mcp
{{- end }}

{{- define "aisoc.databaseUrl" -}}
postgresql+asyncpg://{{ .Values.postgres.username }}:$(POSTGRES_PASSWORD)@{{ .Values.postgres.host }}:{{ .Values.postgres.port }}/{{ .Values.postgres.database }}
{{- end }}

{{- define "aisoc.databaseUrlSync" -}}
postgresql://{{ .Values.postgres.username }}:$(POSTGRES_PASSWORD)@{{ .Values.postgres.host }}:{{ .Values.postgres.port }}/{{ .Values.postgres.database }}
{{- end }}
