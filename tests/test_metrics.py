"""
Тесты для модуля metrics.py
"""

import pytest
import time
import threading
from metrics import Counter, LatencyStats, LatencyMetric, MetricsRegistry, metric, timed
import logging


def test_counter_increment():
    counter = Counter("test_counter")
    assert counter.get() == 0

    counter.inc()
    assert counter.get() == 1

    counter.inc(5)
    assert counter.get() == 6

    with pytest.raises(ValueError, match="количество должно быть >= 0"):
        counter.inc(-1)


def test_latency_stats():
    stats = LatencyStats()
    assert stats.count == 0
    assert stats.total_ms == 0
    assert stats.avg_ms == 0.0

    stats.observe(100)
    assert stats.count == 1
    assert stats.total_ms == 100
    assert stats.min_ms == 100
    assert stats.max_ms == 100
    assert stats.avg_ms == 100.0

    stats.observe(50)
    stats.observe(200)

    assert stats.count == 3
    assert stats.total_ms == 350
    assert stats.min_ms == 50
    assert stats.max_ms == 200
    assert pytest.approx(stats.avg_ms) == 116.6666667


def test_metrics_registry():
    registry = MetricsRegistry()
    counter1 = registry.counter("test_counter")
    counter2 = registry.counter("test_counter")
    assert counter1 is counter2

    counter1.inc(10)
    assert registry.counter("test_counter").get() == 10

    latency = registry.latency("test_latency")
    latency.observe(100)
    latency.observe(200)

    snapshot = registry.snapshot()

    assert "test_counter" in snapshot["counters"]
    assert snapshot["counters"]["test_counter"] == 10

    assert "test_latency" in snapshot["latencies"]
    assert snapshot["latencies"]["test_latency"]["count"] == 2


def test_timed_decorator():
    mock_logger = pytest.Mock(spec=logging.Logger)

    @timed("test_function_ms", logger=mock_logger)
    def test_function(delay=0.05):
        time.sleep(delay)
        return "success"

    result = test_function(0.03)

    assert result == "success"

    latency_data = metric.latency("test_function_ms").snapshot()
    assert latency_data["count"] == 1
    assert latency_data["total_ms"] >= 30
    assert mock_logger.debug.called