from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from frontend.models.ai_provider import AITaskType
from frontend.models.ai_task_result import AITaskRequest
from frontend.services.ai_router import AIRouter
from frontend.services.jp_business_hell_ai import JPBusinessHellAI
from harness.report_writer import write_report

def main():
    router=AIRouter(); checks=[]
    res=router.route(AITaskRequest(AITaskType.SCENARIO_GENERATION,'scenario', privacy_mode='synthetic'))
    checks.append(('choose_provider_by_task', res.ok and res.provider_used))
    checks.append(('gemini_not_only_path', 'offline_demo' in router.providers and 'gemini' in router.providers and len(router.providers)>2))
    app=JPBusinessHellAI(router=router)
    scenario=app.generate_scenario(privacy_mode='synthetic'); feedback=app.grade_answer(scenario,'ちょっと遅れます', privacy_mode='synthetic')
    checks.append(('demo_drill_synthetic', bool(feedback.get('weakness_tags'))))
    checks.append(('strong_calls_reserved', int(router.policy.tier_for(AITaskType.SCENARIO_GENERATION)) < 4 and int(router.policy.tier_for(AITaskType.FINAL_BOSS_JUDGE)) == 3))
    ok=all(v for _,v in checks); write_report('provider_router_eval', {'ok': ok, 'checks': checks, 'tier_report': router.policy.tier_report()})
    print('PASS' if ok else 'FAIL'); return 0 if ok else 1
if __name__=='__main__': raise SystemExit(main())
