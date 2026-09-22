from django.db import migrations

SQL = """
CREATE FUNCTION nominations_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Allocation and verification evidence is append-only' USING ERRCODE = '23514';
END $$;
CREATE TRIGGER nominations_run_history BEFORE UPDATE OR DELETE ON nominations_allocationrun
FOR EACH ROW EXECUTE FUNCTION nominations_history_guard();
CREATE TRIGGER nominations_assessment_history BEFORE UPDATE OR DELETE ON nominations_assessment
FOR EACH ROW EXECUTE FUNCTION nominations_history_guard();
CREATE FUNCTION nominations_inactive_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.is_active AND EXISTS(SELECT 1 FROM nominations_assessment a WHERE a.expert_id=NEW.id
      AND a.status IN ('retired','transferred','deceased','permanent')) THEN
    RAISE EXCEPTION 'Permanent inactivity cannot be reversed' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_inactive BEFORE UPDATE ON experts_expert
FOR EACH ROW EXECUTE FUNCTION nominations_inactive_guard();
"""

REVERSE = """
DROP TRIGGER nominations_inactive ON experts_expert;
DROP FUNCTION nominations_inactive_guard();
DROP TRIGGER nominations_assessment_history ON nominations_assessment;
DROP TRIGGER nominations_run_history ON nominations_allocationrun;
DROP FUNCTION nominations_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("nominations", "0001_initial")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
