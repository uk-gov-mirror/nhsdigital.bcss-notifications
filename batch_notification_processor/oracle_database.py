import logging
import oracledb
import database

from recipient import Recipient


def get_routing_plan_id(batch_id: str) -> str | None:
    with database.cursor() as cursor:
        try:
            result = cursor.callfunc(
                "PKG_NOTIFY_WRAP.f_get_next_batch", oracledb.STRING, [batch_id]
            )
            cursor.connection.commit()
            return result
        except oracledb.Error as e:
            logging.error(
                "Error calling PKG_NOTIFY_WRAP.f_get_next_batch for batch_id %s: %s",
                batch_id,
                e,
            )
            return None


def get_recipients(batch_id: str) -> list[Recipient]:
    recipient_data = []

    with database.cursor() as cursor:
        try:
            cursor.execute(
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
                       postcode,
                       sender_org_name,
                       sender_org_address_line_1,
                       sender_org_address_line_2,
                       sender_org_address_line_3,
                       sender_org_address_line_4,
                       sender_org_address_line_5,
                       sender_org_postcode,
                       sender_org_email
                FROM v_notify_message_queue
                WHERE batch_id = :batch_id
                """,
                {"batch_id": batch_id},
            )
            recipient_data = cursor.fetchall()
        except oracledb.Error as e:
            logging.error("Error retrieving recipients for batch: %s", e)

    return [Recipient(*rd) for rd in recipient_data]


def mark_batch_as_sent(batch_id: str) -> int | None:
    with database.cursor() as cursor:
        try:
            result = cursor.callfunc(
                "PKG_NOTIFY_WRAP.f_update_batch_status",
                oracledb.NUMBER,
                [batch_id, "sending"],
            )
            cursor.connection.commit()
            return result
        except oracledb.Error as e:
            logging.error(
                "Error calling PKG_NOTIFY_WRAP.f_update_batch_status for batch %s: %s",
                batch_id,
                e,
            )
            cursor.connection.rollback()
            return None
