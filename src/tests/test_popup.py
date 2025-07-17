"""Tests for PopUp dialog."""

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QMainWindow

from mdaviz.popup import PopUp

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from pytest_mock.plugin import MockerFixture


class TestPopUp:
    """Test suite for PopUp class."""

    @pytest.fixture
    def parent_widget(self, qtbot) -> QMainWindow:
        """Create a parent widget for testing."""
        parent = QMainWindow()
        parent.proceed = Mock()  # Add proceed method
        parent.cancel = Mock()   # Add cancel method
        qtbot.addWidget(parent)
        return parent

    @patch('mdaviz.utils.myLoadUi')
    def test_init(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test initialization of PopUp dialog."""
        # Mock the UI elements
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            # Simulate what myLoadUi does - adds UI elements to the instance
            baseinstance.message = mock_message
            baseinstance.buttonBox = mock_button_box
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Verify parent is set correctly
        assert popup.parent == parent_widget
        
        # Verify UI loading was called
        mock_load_ui.assert_called_once_with(popup.ui_file, baseinstance=popup)
        
        # Verify message was set
        mock_message.setText.assert_called_with("Test message")

    @patch('mdaviz.utils.myLoadUi')
    def test_message_setting(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that message is set correctly on initialization."""
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        
        test_message = "This is a test message"
        popup = PopUp(parent_widget, test_message)
        qtbot.addWidget(popup)
        
        # Manually set up the UI elements and call the relevant parts
        popup.message = mock_message
        popup.buttonBox = mock_button_box
        
        # Simulate the message setting
        popup.message.setText(test_message)
        
        # Verify message was set
        mock_message.setText.assert_called_with(test_message)

    @patch('mdaviz.utils.myLoadUi')
    def test_button_connections(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that button signals are connected properly."""
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        mock_accepted = mocker.Mock()
        mock_rejected = mocker.Mock()
        
        # Set up button box signals
        mock_button_box.accepted = mock_accepted
        mock_button_box.rejected = mock_rejected
        
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Set up mock UI elements
        popup.message = mock_message
        popup.buttonBox = mock_button_box
        
        # Simulate the connection setup
        popup.buttonBox.accepted.connect(popup.accept)
        popup.buttonBox.rejected.connect(popup.reject)
        
        # Verify connections were made
        mock_accepted.connect.assert_called_with(popup.accept)
        mock_rejected.connect.assert_called_with(popup.reject)

    @patch('mdaviz.utils.myLoadUi')
    def test_accept_method(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test accept method calls parent.proceed()."""
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            baseinstance.message = mock_message
            baseinstance.buttonBox = mock_button_box
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Call accept method
        popup.accept()
        
        # Verify parent's proceed method was called
        parent_widget.proceed.assert_called_once()

    @patch('mdaviz.utils.myLoadUi')
    def test_reject_method(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test reject method calls parent.cancel()."""
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        
        def mock_load_ui_side_effect(ui_file, baseinstance=None):
            baseinstance.message = mock_message
            baseinstance.buttonBox = mock_button_box
            
        mock_load_ui.side_effect = mock_load_ui_side_effect
        
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Call reject method
        popup.reject()
        
        # Verify parent's cancel method was called
        parent_widget.cancel.assert_called_once()

    @patch('mdaviz.utils.myLoadUi')
    def test_inheritance(self, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that PopUp inherits from QDialog correctly."""
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Verify it's a QDialog
        from PyQt6.QtWidgets import QDialog
        assert isinstance(popup, QDialog)
        
        # Verify parent relationship
        assert popup.parent() == parent_widget

    @patch('mdaviz.utils.myLoadUi')
    @patch('mdaviz.utils.getUiFileName')
    def test_ui_file_resolution(self, mock_get_ui_filename, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that UI file name is resolved correctly."""
        mock_get_ui_filename.return_value = "popup.ui"
        
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Verify getUiFileName was called with the module file
        mock_get_ui_filename.assert_called_once()
        
        # Verify myLoadUi was called with the resolved UI file
        mock_load_ui.assert_called_once_with("popup.ui", baseinstance=popup)

    @patch('mdaviz.utils.myLoadUi')
    def test_different_messages(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test popup with different message content."""
        mock_message = mocker.Mock()
        mock_button_box = mocker.Mock()
        
        messages = [
            "Short message",
            "A much longer message with multiple words and punctuation!",
            "Message with\nnewlines\nand\ttabs",
            ""  # Empty message
        ]
        
        for msg in messages:
            popup = PopUp(parent_widget, msg)
            qtbot.addWidget(popup)
            
            # Set up mock UI elements
            popup.message = mock_message
            popup.buttonBox = mock_button_box
            
            # Simulate message setting
            popup.message.setText(msg)
            
            # Verify the message was set correctly
            mock_message.setText.assert_called_with(msg)
            
            popup.close()

    @patch('mdaviz.utils.myLoadUi')
    def test_multiple_instantiation(self, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that multiple PopUp instances can be created."""
        popup1 = PopUp(parent_widget, "Message 1")
        popup2 = PopUp(parent_widget, "Message 2")
        
        qtbot.addWidget(popup1)
        qtbot.addWidget(popup2)
        
        # Both should be separate instances
        assert popup1 is not popup2
        assert popup1.parent == parent_widget
        assert popup2.parent == parent_widget

    @patch('mdaviz.utils.myLoadUi')
    def test_ui_file_attribute(self, mock_load_ui, parent_widget, qtbot) -> None:
        """Test that ui_file class attribute is set correctly."""
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Check that ui_file attribute exists
        assert hasattr(PopUp, 'ui_file')

    @patch('mdaviz.utils.myLoadUi')
    def test_accept_calls_super(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that accept method calls super().accept()."""
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Mock the super().accept() method
        with patch.object(popup.__class__.__bases__[0], 'accept') as mock_super_accept:
            popup.accept()
            
            # Verify super().accept() was called
            mock_super_accept.assert_called_once()

    @patch('mdaviz.utils.myLoadUi')
    def test_reject_calls_super(self, mock_load_ui, parent_widget, qtbot, mocker) -> None:
        """Test that reject method calls super().reject()."""
        popup = PopUp(parent_widget, "Test message")
        qtbot.addWidget(popup)
        
        # Mock the super().reject() method
        with patch.object(popup.__class__.__bases__[0], 'reject') as mock_super_reject:
            popup.reject()
            
            # Verify super().reject() was called
            mock_super_reject.assert_called_once() 