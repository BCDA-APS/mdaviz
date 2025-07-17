"""Tests for ProgressDialog classes."""

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget

from mdaviz.progress_dialog import AsyncProgressDialog, ProgressDialog

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestProgressDialog:
    """Test suite for ProgressDialog class."""

    @pytest.fixture
    def parent_widget(self, qtbot) -> QWidget:
        """Create a parent widget for testing."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_init_default_values(self, parent_widget, qtbot) -> None:
        """Test initialization with default values."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Progress"
        assert dialog.isModal() is True
        assert dialog.minimum() == 0
        assert dialog.maximum() == 100
        assert dialog.value() == 0
        assert dialog._canceled is False
        assert dialog._cancel_callback is None

    def test_init_custom_title(self, parent_widget, qtbot) -> None:
        """Test initialization with custom title."""
        title = "Custom Progress Dialog"
        dialog = ProgressDialog(title=title, parent=parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == title

    def test_init_with_auto_close_false(self, parent_widget, qtbot) -> None:
        """Test initialization with auto_close=False."""
        dialog = ProgressDialog(parent=parent_widget, auto_close=False)
        qtbot.addWidget(dialog)
        
        assert dialog.autoClose() is False

    def test_init_with_auto_reset_false(self, parent_widget, qtbot) -> None:
        """Test initialization with auto_reset=False."""
        dialog = ProgressDialog(parent=parent_widget, auto_reset=False)
        qtbot.addWidget(dialog)
        
        assert dialog.autoReset() is False

    def test_set_cancel_callback(self, parent_widget, qtbot) -> None:
        """Test setting cancel callback."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        callback = Mock()
        dialog.set_cancel_callback(callback)
        
        assert dialog._cancel_callback == callback

    def test_update_progress_basic(self, parent_widget, qtbot) -> None:
        """Test basic progress update."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(QApplication, 'processEvents') as mock_process:
            dialog.update_progress(25, 100, "Processing...")
            
            assert dialog.value() == 25
            assert dialog.labelText() == "Processing..."
            mock_process.assert_called_once()

    def test_update_progress_percentage_calculation(self, parent_widget, qtbot) -> None:
        """Test progress percentage calculation."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(QApplication, 'processEvents'):
            # Test 50% progress
            dialog.update_progress(50, 100)
            assert dialog.value() == 50
            
            # Test different ratio
            dialog.update_progress(3, 4)  # 75%
            assert dialog.value() == 75

    def test_update_progress_with_zero_total(self, parent_widget, qtbot) -> None:
        """Test progress update with zero total (edge case)."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(QApplication, 'processEvents'):
            dialog.update_progress(10, 0)
            assert dialog.value() == 0

    def test_update_progress_default_message(self, parent_widget, qtbot) -> None:
        """Test progress update with default message format."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(QApplication, 'processEvents'):
            dialog.update_progress(25, 100)
            expected_message = "Processing: 25/100 (25%)"
            assert dialog.labelText() == expected_message

    def test_update_progress_when_canceled(self, parent_widget, qtbot) -> None:
        """Test that progress update is ignored when canceled."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        dialog._canceled = True
        initial_value = dialog.value()
        
        with patch.object(QApplication, 'processEvents') as mock_process:
            dialog.update_progress(50, 100, "Should be ignored")
            
            # Values should not change
            assert dialog.value() == initial_value
            mock_process.assert_not_called()

    def test_set_message(self, parent_widget, qtbot) -> None:
        """Test setting progress message."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        message = "Custom message"
        with patch.object(QApplication, 'processEvents') as mock_process:
            dialog.set_message(message)
            
            assert dialog.labelText() == message
            mock_process.assert_called_once()

    def test_on_canceled_without_callback(self, parent_widget, qtbot) -> None:
        """Test cancel handling without callback."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        dialog._on_canceled()
        assert dialog._canceled is True

    def test_on_canceled_with_callback(self, parent_widget, qtbot) -> None:
        """Test cancel handling with callback."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        callback = Mock()
        dialog.set_cancel_callback(callback)
        
        dialog._on_canceled()
        
        assert dialog._canceled is True
        callback.assert_called_once()

    def test_is_canceled(self, parent_widget, qtbot) -> None:
        """Test is_canceled method."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.is_canceled() is False
        
        dialog._canceled = True
        assert dialog.is_canceled() is True

    def test_reset_cancel_state(self, parent_widget, qtbot) -> None:
        """Test resetting cancel state."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        dialog._canceled = True
        assert dialog.is_canceled() is True
        
        dialog.reset_cancel_state()
        assert dialog.is_canceled() is False

    def test_canceled_signal_connection(self, parent_widget, qtbot) -> None:
        """Test that canceled signal is properly connected."""
        dialog = ProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        # Simulate cancel button click by emitting the signal
        with patch.object(dialog, '_on_canceled') as mock_on_canceled:
            dialog.canceled.emit()
            mock_on_canceled.assert_called_once()


class TestAsyncProgressDialog:
    """Test suite for AsyncProgressDialog class."""

    @pytest.fixture
    def parent_widget(self, qtbot) -> QWidget:
        """Create a parent widget for testing."""
        parent = QWidget()
        qtbot.addWidget(parent)
        return parent

    def test_init(self, parent_widget, qtbot) -> None:
        """Test AsyncProgressDialog initialization."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == "Progress"
        assert isinstance(dialog, ProgressDialog)  # Inherits from ProgressDialog

    def test_init_custom_title(self, parent_widget, qtbot) -> None:
        """Test AsyncProgressDialog with custom title."""
        title = "Async Processing"
        dialog = AsyncProgressDialog(title=title, parent=parent_widget)
        qtbot.addWidget(dialog)
        
        assert dialog.windowTitle() == title

    def test_update_progress_async(self, parent_widget, qtbot) -> None:
        """Test asynchronous progress update."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        # Connect signal spy to verify signal emission
        with qtbot.waitSignal(dialog.progress_updated, timeout=1000) as blocker:
            dialog.update_progress_async(50, 100, "Async update")
        
        # Verify signal was emitted with correct arguments
        assert blocker.args == [50, 100, "Async update"]

    def test_set_message_async(self, parent_widget, qtbot) -> None:
        """Test asynchronous message setting."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        message = "Async message"
        with qtbot.waitSignal(dialog.message_updated, timeout=1000) as blocker:
            dialog.set_message_async(message)
        
        assert blocker.args == [message]

    def test_complete_async(self, parent_widget, qtbot) -> None:
        """Test asynchronous completion."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with qtbot.waitSignal(dialog.operation_completed, timeout=1000):
            dialog.complete_async()

    def test_fail_async(self, parent_widget, qtbot) -> None:
        """Test asynchronous failure handling."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        error_msg = "Something went wrong"
        with qtbot.waitSignal(dialog.operation_failed, timeout=1000) as blocker:
            dialog.fail_async(error_msg)
        
        assert blocker.args == [error_msg]

    def test_update_progress_slot(self, parent_widget, qtbot) -> None:
        """Test the progress update slot."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(QApplication, 'processEvents'):
            dialog._update_progress_slot(75, 100, "Slot update")
            
            assert dialog.value() == 75
            assert dialog.labelText() == "Slot update"

    def test_set_message_slot(self, parent_widget, qtbot) -> None:
        """Test the message setting slot."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        message = "Slot message"
        with patch.object(QApplication, 'processEvents'):
            dialog._set_message_slot(message)
            
            assert dialog.labelText() == message

    def test_operation_completed_slot(self, parent_widget, qtbot) -> None:
        """Test the operation completed slot."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        with patch.object(dialog, 'close') as mock_close:
            dialog._operation_completed_slot()
            
            assert dialog.value() == 100
            assert dialog.labelText() == "Operation completed successfully"
            mock_close.assert_called_once()

    def test_operation_failed_slot(self, parent_widget, qtbot) -> None:
        """Test the operation failed slot."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        error_msg = "Test error"
        with patch.object(QTimer, 'singleShot') as mock_timer:
            dialog._operation_failed_slot(error_msg)
            
            expected_text = f"Operation failed: {error_msg}"
            assert dialog.labelText() == expected_text
            
            # Verify timer was set to close dialog after 2 seconds
            mock_timer.assert_called_once()
            args = mock_timer.call_args[0]
            assert args[0] == 2000  # 2000ms = 2 seconds

    def test_signal_slot_connections(self, parent_widget, qtbot) -> None:
        """Test that all signals are properly connected to slots."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        # Test that emitting signals calls the appropriate slots
        with patch.object(dialog, '_update_progress_slot') as mock_update:
            dialog.progress_updated.emit(50, 100, "test")
            mock_update.assert_called_once_with(50, 100, "test")
        
        with patch.object(dialog, '_set_message_slot') as mock_message:
            dialog.message_updated.emit("test message")
            mock_message.assert_called_once_with("test message")
        
        with patch.object(dialog, '_operation_completed_slot') as mock_completed:
            dialog.operation_completed.emit()
            mock_completed.assert_called_once()
        
        with patch.object(dialog, '_operation_failed_slot') as mock_failed:
            dialog.operation_failed.emit("error")
            mock_failed.assert_called_once_with("error")

    def test_inheritance(self, parent_widget, qtbot) -> None:
        """Test that AsyncProgressDialog properly inherits from ProgressDialog."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        # Should have all ProgressDialog functionality
        assert hasattr(dialog, 'update_progress')
        assert hasattr(dialog, 'set_message')
        assert hasattr(dialog, 'is_canceled')
        assert hasattr(dialog, 'reset_cancel_state')
        assert hasattr(dialog, 'set_cancel_callback')
        
        # Should also have async-specific functionality
        assert hasattr(dialog, 'update_progress_async')
        assert hasattr(dialog, 'set_message_async')
        assert hasattr(dialog, 'complete_async')
        assert hasattr(dialog, 'fail_async')

    def test_full_async_workflow(self, parent_widget, qtbot) -> None:
        """Test a complete asynchronous workflow."""
        dialog = AsyncProgressDialog(parent=parent_widget)
        qtbot.addWidget(dialog)
        
        # Test multiple async updates
        with patch.object(QApplication, 'processEvents'):
            dialog.update_progress_async(25, 100, "Starting...")
            dialog.update_progress_async(50, 100, "Halfway done...")
            dialog.update_progress_async(75, 100, "Almost finished...")
            
            # Process the signals
            QApplication.processEvents()
            
            # Should reflect the last update
            assert dialog.value() == 75
            assert dialog.labelText() == "Almost finished..." 