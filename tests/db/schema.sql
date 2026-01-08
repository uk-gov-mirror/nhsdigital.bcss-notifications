ALTER SESSION SET CONTAINER=FREEPDB1;
ALTER SESSION SET CURRENT_SCHEMA=MPI_NOTIFY_USER;

GRANT ALL PRIVILEGES TO MPI_NOTIFY_USER IDENTIFIED BY "test";
GRANT UNLIMITED TABLESPACE TO MPI_NOTIFY_USER;

CREATE TABLESPACE MPI_NOTIFY_USER DATAFILE 'mpi_notify_user.dbf' SIZE 100M AUTOEXTEND ON NEXT 10M MAXSIZE UNLIMITED;

COMMIT;

CREATE TABLE notify_message_queue (
  nhs_number            VARCHAR2 (10) NOT NULL,
  event_status_id       NUMBER (38),
  batch_id              VARCHAR2 (38),
  message_id            VARCHAR2 (38),
  message_definition_id NUMBER (38) NOT NULL,
  message_status        VARCHAR2 (25) NOT NULL,
  subject_id            NUMBER (38),
  event_id              NUMBER (38),
  pio_id                NUMBER (38),
  created_datestamp     TIMESTAMP (6) DEFAULT SYSTIMESTAMP NOT NULL,
  read_datestamp        TIMESTAMP (6),
  bcss_error_id         NUMBER (38),
  address_id            NUMBER (38),
  address_version_id    NUMBER (38),
  address_line_1        VARCHAR2 (40),
  address_line_2        VARCHAR2 (40),
  address_line_3        VARCHAR2 (40),
  address_line_4        VARCHAR2 (40),
  address_line_5        VARCHAR2 (40),
  postcode              VARCHAR2 (12),
  gp_practice_name      VARCHAR2 (100)
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE MPI_NOTIFY_USER
NOCOMPRESS;

CREATE TABLE notify_message_definition (
  message_definition_id         NUMBER (38) NOT NULL,
  routing_plan_id               VARCHAR2 (38) NOT NULL,
  event_status_id               NUMBER (38) NOT NULL,
  message_code                  VARCHAR2 (12) NOT NULL,
  message_name                  VARCHAR2 (100) NOT NULL,
  parameter_id                  NUMBER (38),
  end_date                      DATE,
  audit_reason                  VARCHAR2 (250) NOT NULL,
  variable_text_1               VARCHAR2 (4000),
  prevalent_incident_status_id  NUMBER (38),
  gp_practice_endorsement       VARCHAR2 (1),
  subject_had_cancer_previously VARCHAR2 (1)
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE MPI_NOTIFY_USER
NOCOMPRESS;

CREATE TABLE message_types (
  message_type_id   NUMBER (38) NOT NULL,
  message_type_name VARCHAR2 (100) NOT NULL
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE MPI_NOTIFY_USER
NOCOMPRESS;

CREATE TABLE notify_message_batch (
  batch_id              VARCHAR2 (38) NOT NULL,
  message_definition_id	NUMBER (38) NOT NULL,
  datestamp             TIMESTAMP (6) DEFAULT SYSTIMESTAMP NOT NULL
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE MPI_NOTIFY_USER
NOCOMPRESS;

CREATE TABLE ep_event_status_transition_t (
  key_id          NUMBER (38) NOT NULL,
  event_id        NUMBER (38) NOT NULL,
  from_status_id  NUMBER (38) NOT NULL,
  to_status_id    NUMBER (38) NOT NULL
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE mpi_notify_user
NOCOMPRESS;

COMMIT;

CREATE OR REPLACE PACKAGE MPI_NOTIFY_USER.pkg_notify_wrap AS
  FUNCTION f_get_next_batch (pi_batch_id IN notify_message_batch.batch_id%TYPE)
    RETURN notify_message_definition.routing_plan_id%TYPE;

  FUNCTION f_update_message_status (
    pi_message_id       IN notify_message_queue.message_id%TYPE,
    pi_message_status   IN notify_message_queue.message_status%TYPE
  )
    RETURN message_types.message_type_id%TYPE;

  FUNCTION f_update_batch_status (
    pi_batch_id         IN notify_message_queue.batch_id%TYPE,
    pi_message_status   IN notify_message_queue.message_status%TYPE
  )
    RETURN message_types.message_type_id%TYPE;

END pkg_notify_wrap;
/

CREATE OR REPLACE PACKAGE BODY MPI_NOTIFY_USER.pkg_notify_wrap AS
  FUNCTION f_get_next_batch (pi_batch_id IN notify_message_batch.batch_id%TYPE)
		RETURN notify_message_definition.routing_plan_id%TYPE IS
		v_message_definition_id    notify_message_queue.message_definition_id%TYPE;
		v_routing_plan_id          notify_message_definition.routing_plan_id%TYPE;
		c_function_name            CONSTANT VARCHAR2 (35) := 'PKG_NOTIFY.f_get_next_batch';

	BEGIN
    IF pi_batch_id IS NULL
    THEN
      v_routing_plan_id := NULL;
    ELSE
       BEGIN
          SELECT nmq.message_definition_id,
                 nmd.routing_plan_id
          INTO v_message_definition_id,
               v_routing_plan_id
          FROM notify_message_queue nmq
          INNER JOIN notify_message_definition nmd ON nmd.message_definition_id = nmq.message_definition_id
          WHERE nmq.message_status = 'new'
          ORDER BY nmq.created_datestamp ASC
          FETCH FIRST 1 ROW ONLY;
       EXCEPTION
          WHEN NO_DATA_FOUND
          THEN
             v_message_definition_id := NULL;
             v_routing_plan_id := NULL;
       END;

       IF v_message_definition_id IS NOT NULL
       THEN
          BEGIN
             INSERT INTO notify_message_batch (
                batch_id,
                message_definition_id,
                datestamp
             )
             VALUES (
                pi_batch_id,
                v_message_definition_id,
                SYSTIMESTAMP
             );

             UPDATE notify_message_queue nmq
             SET nmq.batch_id		      = pi_batch_id,
                 nmq.message_status   = 'requested'
             WHERE nmq.message_status = 'new'
             AND nmq.message_definition_id = v_message_definition_id;
          END;
       END IF;
		END IF;

		RETURN v_routing_plan_id;
	END f_get_next_batch;

  FUNCTION f_update_message_status (
    pi_message_id       IN notify_message_queue.message_id%TYPE,
    pi_message_status   IN notify_message_queue.message_status%TYPE
  )
    RETURN message_types.message_type_id%TYPE IS
    v_error_id  message_types.message_type_id%TYPE := 0;
  BEGIN
      UPDATE  notify_message_queue nmq
      SET     nmq.message_status = pi_message_status,
              nmq.read_datestamp = SYSTIMESTAMP
      WHERE     nmq.message_id = pi_message_id;
    RETURN  v_error_id;
  END f_update_message_status;

  FUNCTION f_update_batch_status (
    pi_batch_id         IN notify_message_queue.batch_id%TYPE,
    pi_message_status   IN notify_message_queue.message_status%TYPE
  )
    RETURN message_types.message_type_id%TYPE IS
    v_error_id  message_types.message_type_id%TYPE := 0;
  BEGIN
      UPDATE notify_message_queue nmq
      SET    nmq.message_status = pi_message_status,
             nmq.read_datestamp = SYSTIMESTAMP
      WHERE  nmq.batch_id = pi_batch_id;
    RETURN  v_error_id;
  END f_update_batch_status;

END pkg_notify_wrap;
/

SHOW ERRORS;

COMMIT;

CREATE OR REPLACE VIEW MPI_NOTIFY_USER.v_notify_message_queue
AS
  SELECT  nmq.nhs_number,
          nmq.message_id,
          nmq.batch_id,
          nmd.routing_plan_id,
          nmq.message_status,
          nmd.variable_text_1,
          nmq.address_line_1,
          nmq.address_line_2,
          nmq.address_line_3,
          nmq.address_line_4,
          nmq.address_line_5,
          nmq.postcode,
          nmq.sender_org_name,
          nmq.sender_org_address_line_1,
          nmq.sender_org_address_line_1,
          nmq.sender_org_address_line_1,
          nmq.sender_org_address_line_1,
          nmq.sender_org_address_line_1,
          nmq.sender_org_postcode,
          nmq.sender_org_email
  FROM MPI_NOTIFY_USER.notify_message_queue nmq
      INNER JOIN MPI_NOTIFY_USER.notify_message_definition nmd
         ON nmd.message_definition_id = nmq.message_definition_id;


INSERT INTO MPI_NOTIFY_USER.notify_message_definition (message_definition_id, routing_plan_id, event_status_id, message_code, message_name, parameter_id, end_date, audit_reason, prevalent_incident_status_id, gp_practice_endorsement, subject_had_cancer_previously, variable_text_1) VALUES (
1, 'e43a7d31-a287-485e-b1c2-f53cebbefba3', 11197, 'S1a', 'Pre-invitation: incident subjects with no previous cancer diagnosis', 212, NULL, 'BCSS-18672', 203151, NULL, 'N', 'We offer screening every 2 years to try and find signs of bowel cancer at an early stage when there are no symptoms. This is when treatment can be more effective.');

INSERT INTO MPI_NOTIFY_USER.notify_message_definition (message_definition_id, routing_plan_id, event_status_id, message_code, message_name, parameter_id, end_date, audit_reason, prevalent_incident_status_id, gp_practice_endorsement, subject_had_cancer_previously, variable_text_1) VALUES (
2, 'b22575a8-84fc-40f7-960c-d57975dae039', 11197, 'S1b', 'Pre-invitation: incident subjects with previous cancer diagnosis', 212, NULL, 'BCSS-18672', 203151, NULL, 'Y', 'Routine screening may not be suitable if you are having ongoing care or treatment for a bowel condition, following a previous referral. You can contact us for advice.');


COMMIT;

-- 1. Remove trailing comma in column list
-- 2. Use CREATE TABLE for a table, not a view (don't use v_ prefix for tables)
-- 3. Use schema prefix only if needed (here, it's fine for clarity)

CREATE TABLE MPI_NOTIFY_USER.notify_message_record (
  message_id     VARCHAR2 (38) NOT NULL,
  batch_id       VARCHAR2 (38) NOT NULL,
  message_status VARCHAR2 (25) -- Add this column to match your code expectations
)
RESULT_CACHE (MODE DEFAULT)
TABLESPACE MPI_NOTIFY_USER
NOCOMPRESS;

COMMIT;

-- Insert sample data with real UUIDs and a status
INSERT INTO MPI_NOTIFY_USER.notify_message_record (message_id, batch_id, message_status)
  VALUES ('e5aeb4f8-666a-cd74-0883-1caea4c3f39f', '949f180d-b7a0-14a4-a4ad-62c792c14e46', 'not read');
INSERT INTO MPI_NOTIFY_USER.notify_message_record (message_id, batch_id, message_status)
  VALUES ('966ecc3a-1e6b-5006-1ba6-f5457f496351', 'a9a92820-d538-51cd-a31d-a57d082e8c73', 'not read');

COMMIT;

-- Update the view to include message_status
CREATE OR REPLACE VIEW MPI_NOTIFY_USER.v_notify_message_record AS
SELECT message_id, batch_id, message_status FROM MPI_NOTIFY_USER.notify_message_record;

COMMIT;