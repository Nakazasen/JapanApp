from frontend.services.jp_business_hell_ai import JPBusinessHellAI
from frontend.services.japanese_work_memory import JapaneseWorkLearningMemory

def test_demo_drill_generation_grading_memory(tmp_path):
    memory=JapaneseWorkLearningMemory(tmp_path/'memory.json', mode='synthetic')
    app=JPBusinessHellAI(memory=memory)
    scenario=app.generate_scenario(privacy_mode='synthetic')
    assert scenario['provider_used'] == 'offline_demo'
    feedback=app.grade_answer(scenario, 'ちょっと遅れます', privacy_mode='synthetic')
    for field in ['provider_used','provider_tier','fallback_used','judge_provider','score_total','scores','critical_errors','unnatural_phrases','better_version','vietnamese_explanation','next_drill','weakness_tags']:
        assert field in feedback
    assert feedback['srs_items']
    assert memory.data['weakness_counts']

def test_boss_fight_uses_judge_provider(tmp_path):
    app=JPBusinessHellAI(memory=JapaneseWorkLearningMemory(tmp_path/'memory.json', mode='synthetic'))
    scenario=app.generate_scenario(privacy_mode='synthetic')
    feedback=app.grade_answer(scenario, '申し訳ございません。明日提出します。', boss_fight=True, privacy_mode='synthetic')
    assert feedback['judge_provider']
    assert feedback['provider_tier'] == 3
