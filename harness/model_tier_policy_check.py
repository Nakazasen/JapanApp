from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend.models.ai_provider import AITaskType
from frontend.services.ai_task_policy import AITaskPolicy
from harness.report_writer import write_report

def main():
    p=AITaskPolicy(); checks=[]
    checks.append(('simple_generation_not_tier4', int(p.tier_for(AITaskType.SCENARIO_GENERATION)) < 4))
    checks.append(('nuance_tier2', int(p.tier_for(AITaskType.KEIGO_CORRECTION)) == 2))
    checks.append(('boss_tier3', int(p.tier_for(AITaskType.FINAL_BOSS_JUDGE)) == 3))
    checks.append(('dev_tier4', int(p.tier_for(AITaskType.CODE_GENERATION)) == 4))
    checks.append(('dev_not_language_drill', p.route_for(AITaskType.CODE_GENERATION).get('language_drill_allowed') is False))
    ok=all(v for _,v in checks); write_report('model_tier_policy_check', {'ok': ok, 'checks': checks, 'tier_report': p.tier_report()})
    print('PASS' if ok else 'FAIL'); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
