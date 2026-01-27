import database
from oracledb import Cursor
import logging

from exceptions import MessageUpdateError


def record_message_statuses(json_data: dict) -> dict[str, int]:
    response_counts = {"zero": 0, "non_zero": 0}

    for data in json_data.get("data", []):
        response_code = record_message_status(data)
        if response_code == 0:
            response_counts["zero"] += 1
        else:
            response_counts["non_zero"] += 1

    return response_counts


def record_message_status(json_data: dict) -> int:
    response_code = 0
    message_reference = json_data.get("attributes", {}).get("messageReference")

    if message_reference is not None:
        with database.cursor() as cursor:
            # INFO: Below calls DB function f_update_message_status which also checks for existence of record
            response_code = update_message_status(
                cursor, message_reference
            )

    if response_code > 0:
        logging.error(
            "Error updating status of message %s - oracle error ID %s",
            message_reference,
            response_code,
        )
        raise MessageUpdateError(f"Error updating message {message_reference} status")

    return response_code


def update_message_status(cursor: Cursor, message_reference: str) -> int:
    var = cursor.var(int)

    cursor.execute(
        """
            begin
                :out_val := pkg_notify_wrap.f_update_message_status(:in_val1, :in_val2);
            end;
        """,
        {
            "in_val1": message_reference,
            "in_val2": "read",
            "out_val": var,
        },
    )
    cursor.connection.commit()

    return var.getvalue()
