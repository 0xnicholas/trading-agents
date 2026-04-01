"""
Unit tests for structured logging.
"""
import json
import logging
import sys
import pytest
from tradingagents_crypto.utils.logging import JSONFormatter, setup_logging, get_logger


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def test_format_basic_log(self):
        """Test basic log record formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        result = json.loads(formatter.format(record))

        assert result["level"] == "INFO"
        assert result["message"] == "Test message"
        assert result["service"] == "crypto-trading"
        assert "timestamp" in result

    def test_format_with_context(self):
        """Test log record with context."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Position opened",
            args=(),
            exc_info=None,
        )
        record.context = {"symbol": "BTC", "side": "long"}
        result = json.loads(formatter.format(record))

        assert result["context"]["symbol"] == "BTC"
        assert result["context"]["side"] == "long"

    def test_format_with_trace_id(self):
        """Test log record with trace ID."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.trace_id = "abc123"
        result = json.loads(formatter.format(record))

        assert result["trace_id"] == "abc123"

    def test_format_with_exception(self):
        """Test log record with exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
        result = json.loads(formatter.format(record))

        assert result["level"] == "ERROR"
        assert "exception" in result

    def test_format_debug_level(self):
        """Test DEBUG level formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="",
            lineno=0,
            msg="Debug message",
            args=(),
            exc_info=None,
        )
        result = json.loads(formatter.format(record))

        assert result["level"] == "DEBUG"

    def test_format_empty_trace_id(self):
        """Test that empty trace_id becomes empty string."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test",
            args=(),
            exc_info=None,
        )
        # No trace_id set
        result = json.loads(formatter.format(record))

        assert result["trace_id"] == ""


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_creates_logger(self, tmp_path):
        """Test that setup_logging creates a working logger."""
        setup_logging(level="INFO", log_dir=tmp_path, json_format=False)

        logger = get_logger("test")
        # Logger inherits from root, level is set on root logger
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

    def test_setup_json_format(self, tmp_path):
        """Test setup_logging with JSON format."""
        setup_logging(level="INFO", log_dir=tmp_path, json_format=True)

        logger = get_logger("test_json")
        logger.info("Test message")

    def test_setup_console_only(self):
        """Test setup_logging without log file."""
        setup_logging(level="WARNING", log_dir=None, json_format=False)

        logger = get_logger("console_only")
        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_get_logger_same_name(self):
        """Test that get_logger returns the same logger for same name."""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        assert logger1 is logger2
