from contextlib import contextmanager
import dotenv
import json
import logging
import pytest
import oracledb
import os

dotenv.load_dotenv(".env.test")


@pytest.fixture
def routing_plan_ids():
    return [
        "e43a7d31-a287-485e-b1c2-f53cebbefba3",
        "b22575a8-84fc-40f7-960c-d57975dae039"
    ]


@pytest.fixture
def recipient_data():
    return [
        ("9449304424", "51c33851-5ad6-499d-91f0-38618fb15fcd"),
        ("9449305552", "e6c4a2d8-780e-4d28-a5e5-ee89be535e22"),
        ("9449306621", "83452037-abe2-4b34-acf9-7ba2015cd84b"),
        ("9449306613", "e5fa43a0-37ba-45f6-a4dd-2d9d8b6f66b2"),
        ("9449306605", "360641b3-3258-4076-8d23-3582fcf9ba91"),
    ]


@pytest.fixture
def nhs_notify_message_batch_schema():
    schema_path = os.path.dirname(os.path.abspath(__file__))
    with open(schema_path + "/nhs-notify.json", encoding="utf-8") as f:
        schema = json.load(f)
        return schema["paths"]["/v1/message-batches"]["post"]["requestBody"]["content"]["application/vnd.api+json"]["schema"]


class Helpers:
    @staticmethod
    @contextmanager
    def cursor():
        conn = oracledb.connect(
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            dsn=f"{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_SID')}",
        )
        try:
            yield conn.cursor()
        finally:
            conn.close()

    @staticmethod
    def seed_message_queue(batch_id, recipient_data, message_definition_id=1):
        with Helpers.cursor() as cur:
            cur.execute(
                """
                INSERT INTO notify_message_batch (batch_id, message_definition_id) 
                VALUES (:batch_id, :message_definition_id)
                """,
                batch_id=batch_id,
                message_definition_id=message_definition_id,
            )
            for recipient in recipient_data:
                cur.execute(
                    """
                    INSERT INTO notify_message_queue (
                        nhs_number, message_id, event_status_id, message_definition_id, message_status,
                        subject_id, event_id, pio_id
                    ) VALUES (:nhs_number, :message_reference, 11197, :message_definition_id, 'new', 1, 1, 1)
                    """,
                    nhs_number=recipient[0],
                    message_reference=recipient[1],
                    message_definition_id=message_definition_id,
                )

            cur.connection.commit()

    @staticmethod
    def call_get_next_batch(batch_id):
        with Helpers.cursor() as cur:
            cur.callfunc(
                "PKG_NOTIFY_WRAP.f_get_next_batch", oracledb.STRING, [batch_id]
            )
            cur.connection.commit()

    @staticmethod
    def mark_batch_as_sent(batch_id):
        with Helpers.cursor() as cur:
            cur.callfunc(
                "PKG_NOTIFY_WRAP.f_update_batch_status",
                oracledb.NUMBER,
                [batch_id, "sending"]
            )
            cur.connection.commit()


@pytest.fixture
def helpers():
    return Helpers()


@pytest.fixture(autouse=True)
def reset_db(helpers):
    with helpers.cursor() as cur:
        cur.execute("TRUNCATE TABLE notify_message_queue")
        cur.execute("TRUNCATE TABLE notify_message_batch")
        cur.connection.commit()
        logging.info("Database reset complete.")
