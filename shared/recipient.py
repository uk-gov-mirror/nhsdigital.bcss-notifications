from typing import NamedTuple


class Recipient(NamedTuple):
    nhs_number: str | None = None
    message_id: str | None = None
    batch_id: str | None = None
    routing_plan_id: str | None = None
    message_status: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    address_line_3: str | None = None
    address_line_4: str | None = None
    address_line_5: str | None = None
    postcode: str | None = None
    sender_org_name: str | None = None
    sender_org_address_line_1: str | None = None
    sender_org_address_line_2: str | None = None
    sender_org_address_line_3: str | None = None
    sender_org_address_line_4: str | None = None
    sender_org_address_line_5: str | None = None
    sender_org_postcode: str | None = None
    sender_org_email: str | None = None
