# AI Security Operations Platform (Agentic AI SOC)

## Vision

An enterprise-grade AI Security Operations Platform that unifies
Graylog, Elasticsearch, Loki, Splunk, OpenSearch, and Datadog into an
autonomous investigation platform powered by AI agents.

## Goals

-   Autonomous incident investigation
-   Cross-platform log correlation
-   Root cause analysis
-   RAG-assisted security knowledge
-   Explainable AI
-   Human-in-the-loop approvals
-   Production-ready cloud-native architecture

# Core Capabilities

-   Search all connected log platforms
-   Top-3 keyword extraction
-   Semantic search + hybrid retrieval
-   Parallel log retrieval
-   AI log analysis
-   Timeline generation
-   Root cause detection
-   MITRE ATT&CK mapping
-   IOC extraction
-   Severity prediction
-   Confidence scoring
-   Remediation recommendations
-   Executive & technical reports
-   Streaming responses
-   Saved investigations

# Multi-Agent Architecture

Planner Coordinator Keyword Extractor Retriever Correlator RAG Agent
Analyzer MITRE Mapper Threat Intelligence Agent Reporter Critic Memory

# MCP Server

Expose tools: search_logs search_indices query_platform aggregate
timeline incident_summary lookup_ioc knowledge_search runbook_search

# RAG

Vector DB: - Qdrant Knowledge: - Runbooks - SOPs - Previous incidents -
CVEs - Internal documentation - Security policies

# Frontend

React 19 TypeScript 5.9 Vite Tailwind CSS v4 shadcn/ui React Flow
Cytoscape.js Recharts Monaco Editor Features: - AI Chat - Investigation
Workspace - Agent Execution Graph - Service Dependency Graph -
Timeline - Heatmap - Live Log Stream - Token Stream - Explainability
Panel - Report Export

# Backend

Python 3.13 FastAPI LangGraph Pydantic v2 httpx SQLAlchemy Celery Redis

# APIs

OpenAI-compatible BASE_URL/API_KEY Provider routing Fallback models
Cost-aware routing

# Integrations

Graylog Elasticsearch Loki Splunk OpenSearch Datadog Slack Microsoft
Teams Jira ServiceNow

# Security

OAuth2/OIDC JWT RBAC Audit Logs Secrets Manager Rate Limiting

# Observability

OpenTelemetry Prometheus Grafana Tempo Loki

# Infrastructure

Docker Kubernetes Helm GitHub Actions Terraform

# Testing

pytest Playwright Agent evaluation Load testing Security testing

# Phases

1.  Foundation — **DONE** (FastAPI app, config, logging, Docker Compose baseline)
2.  Connector Framework — **DONE** (base types, registry, parallel search, mock corpus)
3.  Graylog Integration — **DONE** (Graylog connector + mock health/search path)
4.  Multi-Agent Engine — **DONE** (LangGraph / sequential investigation pipeline)
5.  RAG & Vector Search — **DONE** (Qdrant + in-memory fallback, hybrid BM25+vector)
6.  Threat Intelligence — **DONE** (IOC extractors, providers, API surface)
7.  MCP Server — **DONE** (standalone MCP tool server packaging)
8.  Modern Dashboard — **DONE** (React UI: chat, investigations, graphs, reports)
9.  Security & RBAC — **DONE** (JWT auth, roles/permissions, seed users, audit)
10. Observability — **DONE** (OTel collector, Prometheus, Grafana, Tempo, Loki)
11. CI/CD — **DONE** (GitHub Actions CI + GHCR release on `v*` tags)
12. Production Deployment — **DONE** (Helm chart, k8s reference, Terraform local stubs)

# Future

-   Multi-tenancy
-   GraphRAG
-   Temporal workflows
-   Autonomous remediation
-   SOAR integrations
-   Multi-region deployment
-   Fine-grained cost analytics
-   AI evaluation dashboards
-   Plugin SDK
