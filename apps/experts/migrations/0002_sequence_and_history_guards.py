from django.db import migrations

SQL = """
CREATE FUNCTION experts_protect_sequence() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.sequence IS DISTINCT FROM OLD.sequence THEN
    RAISE EXCEPTION 'Expert sequence is immutable' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER experts_sequence_immutable BEFORE UPDATE ON experts_expert
FOR EACH ROW EXECUTE FUNCTION experts_protect_sequence();

CREATE FUNCTION experts_check_history() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  PERFORM id FROM experts_expert WHERE id = NEW.expert_id FOR UPDATE;
  IF NEW.start_date IS NOT NULL AND (NEW.end_date IS NOT NULL OR NEW.is_current) THEN
    IF EXISTS (SELECT 1 FROM experts_appointment a
      WHERE a.expert_id = NEW.expert_id AND a.id <> NEW.id
        AND a.start_date IS NOT NULL AND (a.end_date IS NOT NULL OR a.is_current)
        AND (NEW.end_date IS NULL OR a.start_date < NEW.end_date)
        AND (a.end_date IS NULL OR NEW.start_date < a.end_date)) THEN
      RAISE EXCEPTION 'Known appointment periods overlap' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER experts_appointment_no_overlap BEFORE INSERT OR UPDATE ON experts_appointment
FOR EACH ROW EXECUTE FUNCTION experts_check_history();
"""
REVERSE = """
DROP TRIGGER experts_appointment_no_overlap ON experts_appointment;
DROP FUNCTION experts_check_history();
DROP TRIGGER experts_sequence_immutable ON experts_expert;
DROP FUNCTION experts_protect_sequence();
"""


class Migration(migrations.Migration):
    dependencies = [("experts", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
