from django.db import migrations

SQL = """
CREATE FUNCTION nominations_letter_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Letter identity cannot change or be deleted' USING ERRCODE = '23514';
END $$;
CREATE TRIGGER nominations_letter_history BEFORE UPDATE OR DELETE ON nominations_letter
FOR EACH ROW EXECUTE FUNCTION nominations_letter_history_guard();
CREATE FUNCTION nominations_letter_revision_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Letter revision cannot be deleted' USING ERRCODE = '23514';
  END IF;
  IF OLD.state = 'approved' AND ROW(NEW.letter_id, NEW.revision, NEW.state, NEW.letter_date,
      NEW.source_run_id, NEW.source_selection_id, NEW.source_change_id, NEW.snapshot, NEW.pdf_key,
      NEW.checksum, NEW.approved_by_id, NEW.approved_at) IS DISTINCT FROM ROW(OLD.letter_id,
      OLD.revision, OLD.state, OLD.letter_date, OLD.source_run_id, OLD.source_selection_id,
      OLD.source_change_id, OLD.snapshot, OLD.pdf_key, OLD.checksum, OLD.approved_by_id, OLD.approved_at) THEN
    RAISE EXCEPTION 'Approved letter revision cannot change' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_letter_revision_history BEFORE UPDATE OR DELETE ON nominations_letterrevision
FOR EACH ROW EXECUTE FUNCTION nominations_letter_revision_guard();
CREATE FUNCTION nominations_letter_event_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Letter event cannot change or be deleted' USING ERRCODE = '23514'; END $$;
CREATE TRIGGER nominations_letter_event_history BEFORE UPDATE OR DELETE ON nominations_letterevent
FOR EACH ROW EXECUTE FUNCTION nominations_letter_event_guard();
"""
REVERSE = """
DROP TRIGGER nominations_letter_event_history ON nominations_letterevent;
DROP FUNCTION nominations_letter_event_guard();
DROP TRIGGER nominations_letter_revision_history ON nominations_letterrevision;
DROP FUNCTION nominations_letter_revision_guard();
DROP TRIGGER nominations_letter_history ON nominations_letter;
DROP FUNCTION nominations_letter_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("nominations", "0009_letter_letterrevision_letterevent_and_more")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
