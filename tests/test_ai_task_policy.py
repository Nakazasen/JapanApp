from frontend.models.ai_provider import AITaskType, ModelTier
from frontend.services.ai_task_policy import AITaskPolicy

def test_task_tiers_and_no_tier4_for_simple_generation():
    policy=AITaskPolicy()
    assert policy.tier_for(AITaskType.SCENARIO_GENERATION) == ModelTier.CHEAP_FREE_POOL
    assert policy.tier_for(AITaskType.JAPANESE_NUANCE_REVIEW) == ModelTier.STRONG_LANGUAGE
    assert policy.tier_for(AITaskType.FINAL_BOSS_JUDGE) == ModelTier.JUDGE_CONSENSUS
    assert policy.tier_for(AITaskType.CODE_GENERATION) == ModelTier.DEVELOPMENT_AUDIT
    policy.assert_allowed(AITaskType.SCENARIO_GENERATION)

def test_development_tasks_are_separate_from_language_drills():
    policy=AITaskPolicy()
    for task in [AITaskType.CODE_GENERATION, AITaskType.ARCHITECTURE_REVIEW, AITaskType.AUDIT_REVIEW]:
        policy.assert_allowed(task)
        assert policy.route_for(task).get('language_drill_allowed') is False
