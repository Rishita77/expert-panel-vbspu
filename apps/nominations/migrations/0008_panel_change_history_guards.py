from django.db import migrations

SQL = """
CREATE FUNCTION nominations_panel_change_history_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'Panel change history cannot be deleted' USING ERRCODE = '23514';
  END IF;
  IF OLD.state = 'confirmed' AND ROW(NEW.selection_id, NEW.change_type, NEW.state, NEW.revision,
      NEW.outgoing_member_id, NEW.outgoing_expert_id, NEW.replacement_expert_id, NEW.role,
      NEW.source_run_id, NEW.reason, NEW.verifier, NEW.work_not_occurred, NEW.management_reference,
      NEW.management_date, NEW.vc_reference, NEW.vc_date, NEW.confirmed_by_id, NEW.confirmed_at)
      IS DISTINCT FROM ROW(OLD.selection_id, OLD.change_type, OLD.state, OLD.revision,
      OLD.outgoing_member_id, OLD.outgoing_expert_id, OLD.replacement_expert_id, OLD.role,
      OLD.source_run_id, OLD.reason, OLD.verifier, OLD.work_not_occurred, OLD.management_reference,
      OLD.management_date, OLD.vc_reference, OLD.vc_date, OLD.confirmed_by_id, OLD.confirmed_at) THEN
    RAISE EXCEPTION 'Confirmed panel change cannot change' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER nominations_panel_change_history BEFORE UPDATE OR DELETE ON nominations_panelchange
FOR EACH ROW EXECUTE FUNCTION nominations_panel_change_history_guard();
CREATE FUNCTION nominations_new_ledger_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Ledger history cannot change' USING ERRCODE = '23514'; END $$;
CREATE TRIGGER nominations_replacement_contribution_history BEFORE UPDATE OR DELETE ON nominations_replacementcontribution
FOR EACH ROW EXECUTE FUNCTION nominations_new_ledger_guard();
CREATE TRIGGER nominations_utilisation_reversal_history BEFORE UPDATE OR DELETE ON nominations_utilisationreversal
FOR EACH ROW EXECUTE FUNCTION nominations_new_ledger_guard();
"""
REVERSE = """
DROP TRIGGER nominations_utilisation_reversal_history ON nominations_utilisationreversal;
DROP TRIGGER nominations_replacement_contribution_history ON nominations_replacementcontribution;
DROP FUNCTION nominations_new_ledger_guard();
DROP TRIGGER nominations_panel_change_history ON nominations_panelchange;
DROP FUNCTION nominations_panel_change_history_guard();
"""


class Migration(migrations.Migration):
    dependencies = [("nominations", "0007_utilisationreversal_reversal_has_one_contribution")]
    operations = [migrations.RunSQL(SQL, REVERSE)]
