from django.db import migrations

SQL = """
CREATE FUNCTION nominations_final_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Final selection history cannot be deleted' USING ERRCODE = '23514';
  END IF;
  IF OLD.state = 'locked' AND ROW(NEW.request_id, NEW.source_run_id, NEW.state, NEW.revision,
      NEW.management_reference, NEW.management_date, NEW.vc_reference, NEW.vc_date,
      NEW.locked_by_id, NEW.locked_at) IS DISTINCT FROM ROW(OLD.request_id, OLD.source_run_id,
      OLD.state, OLD.revision, OLD.management_reference, OLD.management_date, OLD.vc_reference,
      OLD.vc_date, OLD.locked_by_id, OLD.locked_at) THEN
    RAISE EXCEPTION 'Locked selection cannot change' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_final_history BEFORE UPDATE OR DELETE ON nominations_finalselection
FOR EACH ROW EXECUTE FUNCTION nominations_final_history_guard();
CREATE FUNCTION nominations_member_lock_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS(SELECT 1 FROM nominations_finalselection s WHERE s.id=COALESCE(NEW.selection_id, OLD.selection_id) AND s.state='locked') THEN
    RAISE EXCEPTION 'Locked membership cannot change' USING ERRCODE = '23514';
  END IF;
  RETURN COALESCE(NEW, OLD);
END $$;
CREATE TRIGGER nominations_member_lock BEFORE UPDATE OR DELETE ON nominations_finalmember
FOR EACH ROW EXECUTE FUNCTION nominations_member_lock_guard();
CREATE FUNCTION nominations_utilisation_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Utilisation entry cannot change' USING ERRCODE = '23514'; END $$;
CREATE TRIGGER nominations_utilisation_history BEFORE UPDATE OR DELETE ON nominations_utilisationentry
FOR EACH ROW EXECUTE FUNCTION nominations_utilisation_guard();
"""
REVERSE = """
DROP TRIGGER nominations_utilisation_history ON nominations_utilisationentry;
DROP FUNCTION nominations_utilisation_guard();
DROP TRIGGER nominations_member_lock ON nominations_finalmember;
DROP FUNCTION nominations_member_lock_guard();
DROP TRIGGER nominations_final_history ON nominations_finalselection;
DROP FUNCTION nominations_final_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("nominations", "0003_final_selection")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
