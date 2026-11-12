from django.db import migrations

SQL = """
CREATE FUNCTION nominations_release_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP <> 'INSERT' THEN
    RAISE EXCEPTION 'Registrar releases are immutable' USING ERRCODE = '23514';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM nominations_letterrevision r
    JOIN nominations_letter l ON l.id = r.letter_id
    JOIN nominations_finalselection s ON s.id = NEW.selection_id
    WHERE r.id = NEW.letter_revision_id AND r.source_selection_id = s.id
      AND r.state = 'approved' AND l.kind = 'final' AND s.state = 'locked'
      AND l.request_id = s.request_id
  ) THEN
    RAISE EXCEPTION 'Release requires the matching approved final letter and locked selection'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_release_history BEFORE INSERT OR UPDATE OR DELETE ON nominations_finalrelease
FOR EACH ROW EXECUTE FUNCTION nominations_release_guard();
"""

class Migration(migrations.Migration):
    dependencies = [("nominations", "0013_final_release")]
    operations = [migrations.RunSQL(SQL, """
        DROP TRIGGER nominations_release_history ON nominations_finalrelease;
        DROP FUNCTION nominations_release_guard();
    """)]
