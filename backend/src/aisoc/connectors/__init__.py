"""Log platform connectors."""

from aisoc.connectors.base import (
    AggregateResult,
    BaseLogConnector,
    LogConnector,
    LogEvent,
    SearchQuery,
    TimelineEvent,
)
from aisoc.connectors.datadog import DatadogConnector
from aisoc.connectors.elasticsearch import ElasticsearchConnector
from aisoc.connectors.graylog import GraylogConnector
from aisoc.connectors.loki import LokiConnector
from aisoc.connectors.opensearch import OpenSearchConnector
from aisoc.connectors.registry import (
    ConnectorRegistry,
    get_all_connectors,
    get_registry,
    parallel_search,
    reset_registry,
)
from aisoc.connectors.splunk import SplunkConnector

__all__ = [
    "AggregateResult",
    "BaseLogConnector",
    "ConnectorRegistry",
    "DatadogConnector",
    "ElasticsearchConnector",
    "GraylogConnector",
    "LogConnector",
    "LogEvent",
    "LokiConnector",
    "OpenSearchConnector",
    "SearchQuery",
    "SplunkConnector",
    "TimelineEvent",
    "get_all_connectors",
    "get_registry",
    "parallel_search",
    "reset_registry",
]
