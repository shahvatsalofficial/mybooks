from abc import ABC, abstractmethod

class BaseMetricsCollector(ABC):
    @abstractmethod
    def record_gauge(self, name: str, value: float) -> None:
        pass

class PrometheusCollector(BaseMetricsCollector):
    def record_gauge(self, name: str, value: float) -> None:
        # Implementation details...
        pass
