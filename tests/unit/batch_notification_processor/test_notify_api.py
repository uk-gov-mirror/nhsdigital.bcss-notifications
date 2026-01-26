import notify_api
from recipient import Recipient
import pytest
import requests_mock
from unittest.mock import patch


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("NOTIFY_API_BASE_URL", "http://example.com")
    monkeypatch.setenv("APPLICATION_ID", "application_id")
    monkeypatch.setenv("API_KEY", "api_key")


@patch("access_token.get_token", return_value="access_token")
def test_send_batch_message(mock_get_token):
    with requests_mock.Mocker() as rm:
        adapter = rm.post(
            "http://example.com/comms/v1/message-batches",
            status_code=201,
            json={"data": {"id": "batch_id"}},
        )

        notify_api.send_batch_message(
            "batch_id",
            "routing_config_id",
            [
                Recipient(
                    "0000000000", "message_reference_0", "batch_id_0", "requested",
                    "routing_config_id_0", "address_line_01", "address_line_02",
                    "address_line_03", "address_line_04", "address_line_05", "postcode_0",
                    "sender_org_name_0", "sender_org_address_line_01", "sender_org_address_line_02",
                    "sender_org_address_line_03", "sender_org_address_line_04", "sender_org_address_line_05",
                    "sender_org_postcode_0", "sender_org_email_0"
                ),
                Recipient(
                    "1111111111", "message_reference_1", "batch_id_1", "requested",
                    "routing_config_id_1", "address_line_11", "address_line_12",
                    "address_line_13", "address_line_14", "address_line_15", "postcode_1",
                    "sender_org_name_1", "sender_org_address_line_11", "sender_org_address_line_12",
                    "sender_org_address_line_13", "sender_org_address_line_14", "sender_org_address_line_15",
                    "sender_org_postcode_1", "sender_org_email_1"
                ),
            ]
        )
        assert adapter.last_request.url == "http://example.com/comms/v1/message-batches"
        assert adapter.last_request.headers["authorization"] == "Bearer access_token"
        assert adapter.last_request.json() == {
            "data": {
                "type": "MessageBatch",
                "attributes": {
                    "routingPlanId": "routing_config_id",
                    "messageBatchReference": "batch_id",
                    "messages": [
                        {
                            "recipient": {"nhsNumber": "0000000000"},
                            "messageReference": "message_reference_0",
                            "personalisation": {
                                "address_line_1_bcss": "address_line_01",
                                "address_line_2_bcss": "address_line_02",
                                "address_line_3_bcss": "address_line_03",
                                "address_line_4_bcss": "address_line_04",
                                "address_line_5_bcss": "address_line_05",
                                "address_line_6_bcss": "postcode_0",
                                # "sender_org_name_bcss": "sender_org_name_0",
                                # "sender_org_address_line_1_bcss": "sender_org_address_line_01",
                                # "sender_org_address_line_2_bcss": "sender_org_address_line_02",
                                # "sender_org_address_line_3_bcss": "sender_org_address_line_03",
                                # "sender_org_address_line_4_bcss": "sender_org_address_line_04",
                                # "sender_org_address_line_5_bcss": "sender_org_address_line_05",
                                # "sender_org_postcode_bcss": "sender_org_postcode_0",
                                "sender_org_email_bcss": "sender_org_email_0",
                            },
                        },
                        {
                            "recipient": {"nhsNumber": "1111111111"},
                            "messageReference": "message_reference_1",
                            "personalisation": {
                                "address_line_1_bcss": "address_line_11",
                                "address_line_2_bcss": "address_line_12",
                                "address_line_3_bcss": "address_line_13",
                                "address_line_4_bcss": "address_line_14",
                                "address_line_5_bcss": "address_line_15",
                                "address_line_6_bcss": "postcode_1",
                                # "sender_org_name_bcss": "sender_org_name_1",
                                # "sender_org_address_line_1_bcss": "sender_org_address_line_11",
                                # "sender_org_address_line_2_bcss": "sender_org_address_line_12",
                                # "sender_org_address_line_3_bcss": "sender_org_address_line_13",
                                # "sender_org_address_line_4_bcss": "sender_org_address_line_14",
                                # "sender_org_address_line_5_bcss": "sender_org_address_line_15",
                                # "sender_org_postcode_bcss": "sender_org_postcode_1",
                                "sender_org_email_bcss": "sender_org_email_1",
                            },
                        },
                    ],
                },
            },
        }


def test_generate_batch_message_request_body():
    recipients = [
        Recipient("0000000000", "message_reference_0", "requested"),
        Recipient("1111111111", "message_reference_1", "requested"),
    ]

    message_batch = notify_api.generate_batch_message_request_body("routing_config_id", "batch_reference", recipients)

    assert message_batch["data"]["attributes"]["routingPlanId"] == "routing_config_id"
    assert message_batch["data"]["attributes"]["messageBatchReference"] == "batch_reference"
    assert len(message_batch["data"]["attributes"]["messages"]) == 2
    assert message_batch["data"]["attributes"]["messages"][0]["recipient"]["nhsNumber"] == "0000000000"
    assert message_batch["data"]["attributes"]["messages"][0]["messageReference"] == "message_reference_0"
    assert message_batch["data"]["attributes"]["messages"][1]["recipient"]["nhsNumber"] == "1111111111"
    assert message_batch["data"]["attributes"]["messages"][1]["messageReference"] == "message_reference_1"


def test_generate_message():
    recipient = Recipient(
        "0000000000", "message_reference_0", "batch_id_0", "requested",
        "routing_config_id_0", "address_line_01", "address_line_02",
        "address_line_03", "address_line_04", "address_line_05", "postcode_0",
        "sender_org_name_0", "sender_org_address_line_01", "sender_org_address_line_02",
        "sender_org_address_line_03", "sender_org_address_line_04", "sender_org_address_line_05",
        "sender_org_postcode_0", "sender_org_email_0"
    )

    message = notify_api.generate_message(recipient)

    assert message["messageReference"] == "message_reference_0"
    assert message["recipient"]["nhsNumber"] == "0000000000"
    assert message["personalisation"] == {
        "address_line_1_bcss": "address_line_01",
        "address_line_2_bcss": "address_line_02",
        "address_line_3_bcss": "address_line_03",
        "address_line_4_bcss": "address_line_04",
        "address_line_5_bcss": "address_line_05",
        "address_line_6_bcss": "postcode_0",
        # "sender_org_name_bcss": "sender_org_name_0",
        # "sender_org_address_line_1_bcss": "sender_org_address_line_01",
        # "sender_org_address_line_2_bcss": "sender_org_address_line_02",
        # "sender_org_address_line_3_bcss": "sender_org_address_line_03",
        # "sender_org_address_line_4_bcss": "sender_org_address_line_04",
        # "sender_org_address_line_5_bcss": "sender_org_address_line_05",
        # "sender_org_postcode_bcss": "sender_org_postcode_0",
        "sender_org_email_bcss": "sender_org_email_0",
    }


def test_generate_message_with_partial_data():
    recipient = Recipient(
        "0000000000", "message_reference_0", "batch_id_0", "requested",
        "routing_config_id_0"
    )

    message = notify_api.generate_message(recipient)

    assert message["messageReference"] == "message_reference_0"
    assert message["recipient"]["nhsNumber"] == "0000000000"
    assert message["personalisation"] == {
        "address_line_1_bcss": "",
        "address_line_2_bcss": "",
        "address_line_3_bcss": "",
        "address_line_4_bcss": "",
        "address_line_5_bcss": "",
        "address_line_6_bcss": "",
        # "sender_org_name_bcss": "",
        # "sender_org_address_line_1_bcss": "",
        # "sender_org_address_line_2_bcss": "",
        # "sender_org_address_line_3_bcss": "",
        # "sender_org_address_line_4_bcss": "",
        # "sender_org_address_line_5_bcss": "",
        # "sender_org_postcode_bcss": "",
        "sender_org_email_bcss": "",
    }
