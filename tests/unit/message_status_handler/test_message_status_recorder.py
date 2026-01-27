from unittest.mock import Mock, patch
import pytest

import message_status_recorder


@patch("message_status_recorder.record_message_status")
def test_record_message_statuses(mock_record_message_status):
    """Test the record_message_statuses function with multiple message status records."""
    mock_record_message_status.side_effect = [0, 1]

    json_data = {
        "data": [
            {"attributes": {"messageReference": "message_reference_1"}},
            {"attributes": {"messageReference": "message_reference_2"}},
        ]
    }

    response_codes = message_status_recorder.record_message_statuses(json_data)

    assert response_codes == {
        "zero": 1,
        "non_zero": 1,
    }
    assert mock_record_message_status.call_count == 2
    mock_record_message_status.assert_any_call(
        {"attributes": {"messageReference": "message_reference_1"}}
    )
    mock_record_message_status.assert_any_call(
        {"attributes": {"messageReference": "message_reference_2"}}
    )


@patch("message_status_recorder.update_message_status", return_value=12)
@patch("database.cursor")
def test_record_message_status(
    mock_cursor, mock_update_message_status
):
    """Test the record_message_status calls update_message_status function."""
    json_data = {"attributes": {"messageReference": "message_reference_1"}}

    with pytest.raises(message_status_recorder.MessageUpdateError):
        message_status_recorder.record_message_status(json_data)

    assert mock_update_message_status.call_count == 1
    mock_update_message_status.assert_any_call(
        mock_cursor().__enter__(), "message_reference_1"
    )


def test_record_message_status_no_message_reference():
    """Test the record_message_status when no message reference is provided."""
    json_data = {"attributes": {}}

    response_code = message_status_recorder.record_message_status(json_data)

    assert response_code == 0

@patch("database.cursor")
def test_update_message_status(mock_cursor):
    """Test the update_message_status function."""
    mock_cursor_contextmanager = mock_cursor().__enter__()
    mock_var = Mock(getvalue=Mock(return_value=12))
    mock_cursor_contextmanager.var.return_value = mock_var

    response_code = message_status_recorder.update_message_status(
        mock_cursor_contextmanager, "message_reference_1"
    )

    assert mock_cursor_contextmanager.execute.call_count == 1
    assert response_code == 12
    mock_cursor_contextmanager.execute.assert_called_once_with(
        """
            begin
                :out_val := pkg_notify_wrap.f_update_message_status(:in_val1, :in_val2);
            end;
        """,
        {
            "in_val1": "message_reference_1",
            "in_val2": "read",
            "out_val": mock_var,
        },
    )
