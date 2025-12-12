from unittest.mock import patch, Mock

import pytest
import oracledb
import uuid

from recipient import Recipient
import oracle_database


@pytest.fixture
def mock_db_credentials(monkeypatch):
    monkeypatch.setenv("DATABASE_USER", "user")
    monkeypatch.setenv("DATABASE_PASSWORD", "password")
    monkeypatch.setenv("DATABASE_HOST", "host")
    monkeypatch.setenv("DATABASE_PORT", "port")
    monkeypatch.setenv("DATABASE_SID", "sid")


@patch("oracle_database.database", autospec=True)
def test_get_routing_plan_id(mock_database):
    expected_routing_plan_id = str(uuid.uuid4())
    batch_id = "1234"
    mock_cursor = mock_database.cursor().__enter__()
    mock_cursor.callfunc = Mock(return_value=expected_routing_plan_id)

    routing_plan_id = oracle_database.get_routing_plan_id(batch_id)

    mock_cursor.callfunc.assert_called_with(
        "PKG_NOTIFY_WRAP.f_get_next_batch", oracledb.STRING, [batch_id]
    )
    assert routing_plan_id == expected_routing_plan_id


@patch("oracle_database.database", autospec=True)
def test_get_recipients(mock_database):
    raw_recipient_data = [
        (
            "1111111111",
            "message_reference_1",
        ),
        (
            "2222222222",
            "message_reference_2",
        ),
    ]

    mock_cursor = mock_database.cursor().__enter__()
    mock_cursor.fetchall = Mock(return_value=raw_recipient_data)

    batch_id = "1234"

    recipients = oracle_database.get_recipients(batch_id)

    mock_cursor.execute.assert_called_with(
        """
                SELECT nhs_number,
                       message_id,
                       batch_id,
                       routing_plan_id,
                       message_status,
                       address_line_1,
                       address_line_2,
                       address_line_3,
                       address_line_4,
                       address_line_5,
                       postcode
                FROM v_notify_message_queue
                WHERE batch_id = :batch_id
                """,
        {"batch_id": batch_id},
    )

    assert len(recipients) == 2
    assert isinstance(recipients[0], Recipient)
    assert recipients[0].nhs_number == "1111111111"
    assert recipients[0].message_id == "message_reference_1"
    assert isinstance(recipients[1], Recipient)
    assert recipients[1].nhs_number == "2222222222"
    assert recipients[1].message_id == "message_reference_2"


@patch("oracle_database.database", autospec=True)
def test_mark_batch_as_sent(mock_database):
    batch_id = "1234"

    mock_cursor = mock_database.cursor().__enter__()

    oracle_database.mark_batch_as_sent(batch_id)

    mock_cursor.callfunc.assert_called_with(
        "PKG_NOTIFY_WRAP.f_update_batch_status",
        oracledb.NUMBER,
        [batch_id, "sending"],
    )
    mock_cursor.connection.commit.assert_called_once()


@patch("oracle_database.database", autospec=True)
def test_mark_batch_as_sent_rollback(mock_database):
    mock_cursor = mock_database.cursor().__enter__()
    mock_cursor.callfunc.side_effect = oracledb.Error("Database error")

    result = oracle_database.mark_batch_as_sent("1234")

    assert result is None

    mock_cursor.connection.rollback.assert_called_once()
