from django.db import migrations


SQL = """
CREATE FUNCTION nominations_final_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Final selection history cannot be deleted' USING ERRCODE = '23514';
  END IF;
  IF OLD.state = 'locked' AND ROW(
      NEW.request_id, NEW.source_run_id, NEW.state, NEW.revision,
      NEW.vc_reference, NEW.locked_by_id, NEW.locked_at
  ) IS DISTINCT FROM ROW(
      OLD.request_id, OLD.source_run_id, OLD.state, OLD.revision,
      OLD.vc_reference, OLD.locked_by_id, OLD.locked_at
  ) THEN
    RAISE EXCEPTION 'Locked selection cannot change' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_final_history BEFORE UPDATE OR DELETE ON nominations_finalselection
FOR EACH ROW EXECUTE FUNCTION nominations_final_history_guard();
"""

REVERSE = """
DROP TRIGGER IF EXISTS nominations_final_history ON nominations_finalselection;
DROP FUNCTION IF EXISTS nominations_final_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("nominations", "0011_remove_finalreviewevent_actor_and_more")]

    operations = [migrations.RunSQL(SQL, REVERSE)]
