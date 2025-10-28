#!/usr/bin/env python3
"""
동화 나노바나나 애플리케이션 테스트 스크립트
"""

import sys
import asyncio
from app import StoryTeller

async def test_storyteller_basic():
    """StoryTeller 기본 기능 테스트"""
    print("🧪 StoryTeller 기본 기능 테스트...")
    
    storyteller = StoryTeller()
    
    # 1. 초기 상태 확인
    assert storyteller.story_stage == "setup"
    assert len(storyteller.story_context) == 0
    print("✅ 초기 상태 정상")
    
    # 2. 사용자 정보 설정
    storyteller.learning_subject = "숫자"
    storyteller.user_profile = "6살 호기심 많은 아이"
    storyteller.favorite_topic = "강아지와 파란색"
    print("✅ 사용자 정보 설정 완료")
    
    # 3. 입력 검증 테스트
    valid, msg = storyteller.validate_input("숫자", "input_subject")
    assert valid == True
    print("✅ 입력 검증 통과")
    
    # 4. 캐릭터 이름 추출 테스트
    character_name = storyteller.extract_character_name_from_story("테스트 스토리")
    assert character_name in ["멍멍이", "꼬마", "아이", "친구", "탐험가"]
    print(f"✅ 캐릭터 이름 추출: {character_name}")
    
    # 5. 컨텍스트 관리 테스트
    storyteller.add_to_story_context("첫 번째 이야기", "사용자 입력1")
    storyteller.add_to_story_context("두 번째 이야기", "사용자 입력2")
    assert len(storyteller.story_context) == 2
    print("✅ 스토리 컨텍스트 관리 정상")
    
    # 6. 진행도 표시 테스트
    progress = storyteller.get_progress_indicator()
    assert "🟢" in progress
    print(f"✅ 진행도 표시: {progress}")
    
    # 7. 사용자 의도 분석 테스트
    intent = storyteller.analyze_user_intent("친구를 만나고 싶어요")
    assert intent == "social_interaction"
    print(f"✅ 의도 분석: {intent}")
    
    print("🎉 StoryTeller 기본 기능 테스트 모두 통과!\n")

async def test_error_handling():
    """에러 처리 테스트"""
    print("🛡️ 에러 처리 테스트...")
    
    storyteller = StoryTeller()
    
    # 1. 입력 검증 실패 테스트
    valid, msg = storyteller.validate_input("", "input_subject")
    assert valid == False
    print("✅ 빈 입력 검증 실패 처리")
    
    valid, msg = storyteller.validate_input("a", "input_subject")
    assert valid == False
    print("✅ 너무 짧은 입력 검증 실패 처리")
    
    valid, msg = storyteller.validate_input("a" * 101, "input_subject")
    assert valid == False
    print("✅ 너무 긴 입력 검증 실패 처리")
    
    # 2. 복구 제안 테스트
    suggestions = storyteller.get_recovery_suggestions("input_subject")
    assert len(suggestions) > 0
    print(f"✅ 복구 제안 생성: {len(suggestions)}개")
    
    # 3. 도움말 메뉴 테스트
    help_menu = await storyteller.show_help_menu()
    assert "도움말" in help_menu
    assert "처음부터" in help_menu
    print("✅ 도움말 메뉴 생성")
    
    print("🎉 에러 처리 테스트 모두 통과!\n")

async def test_story_generation():
    """스토리 생성 테스트 (API 호출 없이)"""
    print("📚 스토리 생성 로직 테스트...")
    
    storyteller = StoryTeller()
    storyteller.learning_subject = "색깔"
    storyteller.user_profile = "5살 창의적인 아이"
    storyteller.favorite_topic = "고양이와 분홍색"
    storyteller.character_name = "야옹이"
    
    # 1. 이미지 생성 여부 결정 테스트
    assert storyteller.should_generate_image(1) == True
    assert storyteller.should_generate_image(2) == False
    assert storyteller.should_generate_image(3) == True
    assert storyteller.should_generate_image(4) == False
    assert storyteller.should_generate_image(6) == True
    print("✅ 이미지 생성 여부 결정 로직")
    
    # 2. 캐릭터 일관성 정보 테스트
    char_info = storyteller.get_character_consistency_info()
    assert "야옹이" in char_info
    assert "색깔" in char_info
    print("✅ 캐릭터 일관성 정보 생성")
    
    # 3. 학습 진행도 테스트
    storyteller.add_to_story_context("테스트 스토리 1", "입력1")
    learning_info = storyteller.get_learning_progression()
    assert learning_info["main_subject"] == "색깔"
    assert learning_info["chapters_count"] == 1
    print("✅ 학습 진행도 추적")
    
    print("🎉 스토리 생성 로직 테스트 모두 통과!\n")

def test_ui_helpers():
    """UI 도우미 함수 테스트"""
    print("🎨 UI 도우미 함수 테스트...")
    
    storyteller = StoryTeller()
    
    # 1. 제안 시스템 테스트
    suggestions = storyteller.get_helpful_suggestions("learning_focus")
    assert len(suggestions) == 3
    assert any("배우" in s for s in suggestions)
    print("✅ 학습 중심 제안 생성")
    
    suggestions = storyteller.get_helpful_suggestions("social_interaction")
    assert any("친구" in s for s in suggestions)
    print("✅ 사회적 상호작용 제안 생성")
    
    # 2. 진행도 표시 테스트
    storyteller.add_to_story_context("테스트", "입력")
    progress = storyteller.get_progress_indicator()
    assert "🟢" in progress and "⚪" in progress
    print("✅ 진행도 시각적 표시")
    
    print("🎉 UI 도우미 함수 테스트 모두 통과!\n")

async def run_all_tests():
    """모든 테스트 실행"""
    print("🚀 동화 나노바나나 전체 테스트 시작!\n")
    
    try:
        await test_storyteller_basic()
        await test_error_handling()
        await test_story_generation()
        test_ui_helpers()
        
        print("🎉🎉🎉 모든 테스트 통과! 동화 나노바나나 준비 완료! 🍌📚")
        print("\n✨ 주요 기능 확인 완료:")
        print("  • 3단계 사용자 입력 시스템")
        print("  • 입력 검증 및 에러 처리")
        print("  • 맞춤형 스토리 생성 로직")
        print("  • 컨텍스트 기반 연속 스토리")
        print("  • 이미지 생성 최적화")
        print("  • 사용자 친화적 UI/UX")
        print("  • 종합적 에러 핸들링")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)