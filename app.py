import chainlit as cl
import google.generativeai as genai
import os
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import asyncio
import mimetypes

# 환경변수 로드
load_dotenv()

# API 키 설정
gemini_api_key = os.getenv('GEMINI_API_KEY')

# google.generativeai 설정
genai.configure(api_key=gemini_api_key)
text_model = genai.GenerativeModel('gemini-2.5-flash')

class StoryTeller:
    def __init__(self):
        self.story_context = []
        self.current_chapter = 0
        self.story_stage = "setup"  # setup, story1, story2, story3, chatbot
        self.user_profile = {}
        self.story_choices = []
        self.learning_subject = ""
        self.character_name = ""
        self.favorite_topic = ""
        self.current_question = ""
        self.correct_answer = ""
        # 캐릭터 일관성을 위한 디자인 정보 저장
        self.character_description = ""
        self.character_design_seeds = []
        # 입력 검증을 위한 상태 추가
        self.input_attempts = 0
        self.max_attempts = 3
        
    def validate_input(self, input_text, stage):
        """입력값 검증 함수"""
        if not input_text or input_text.strip() == "":
            return False, "입력이 비어있습니다. 다시 입력해주세요."
        
        if len(input_text.strip()) < 2:
            return False, "너무 짧습니다. 조금 더 자세히 알려주세요."
        
        if len(input_text.strip()) > 100:
            return False, "너무 깁니다. 간단히 요약해서 알려주세요."
        
        # 단계별 특별 검증
        if stage == "input_subject":
            # 학습 주제는 적절한 교육 내용인지 확인
            if any(word in input_text.lower() for word in ['욕설', '폭력', '성인']):
                return False, "적절하지 않은 내용입니다. 학습에 도움이 되는 주제를 입력해주세요."
        
        return True, "검증 성공"
    
    def reset_input_attempts(self):
        """입력 시도 횟수 초기화"""
        self.input_attempts = 0
    
    async def generate_initial_story(self):
        """사용자 정보를 바탕으로 초기 스토리 생성"""
        try:
            # 사용자 맞춤형 스토리 프롬프트 구성
            story_prompt = f"""
            경계선 지능 아동을 위한 개인 맞춤형 동화를 만들어주세요.
            
            사용자 정보:
            - 학습 주제: {self.learning_subject}
            - 사용자 특성: {self.user_profile}
            - 좋아하는 것들: {self.favorite_topic}
            
            동화 작성 가이드라인:
            1. 5-6세 아이가 이해할 수 있는 쉬운 언어 사용
            2. 한 문장당 10-15단어 이내로 짧게 구성
            3. {self.learning_subject} 학습 요소를 자연스럽게 포함
            4. {self.favorite_topic} 요소를 주인공이나 배경에 활용
            5. 따뜻하고 긍정적인 분위기 유지
            6. 아이가 상호작용할 수 있는 질문이나 선택 상황 포함
            
            스토리 구조:
            - 주인공 소개 (사용자 특성 반영)
            - 문제 상황 또는 모험의 시작
            - 학습 요소가 포함된 첫 번째 도전
            - 다음 단계로 이어질 수 있는 열린 결말
            
            200자 내외의 짧은 첫 번째 에피소드를 작성해주세요.
            """
            
            response = text_model.generate_content(story_prompt)
            return response.text
            
        except Exception as e:
            print(f"초기 스토리 생성 오류: {str(e)}")
            error_message = await self.handle_error_gracefully("api_error", str(e), "초기 스토리 생성")
            await cl.Message(content=error_message).send()
            
            return f"""
            안녕하세요! 저는 {self.favorite_topic}을 좋아하는 친구예요! 
            오늘은 {self.learning_subject}에 대해 재미있는 모험을 떠나볼 거예요.
            
            어떤 일이 일어날지 궁금하지 않나요? 
            함께 모험을 시작해보아요!
            """
    
    def extract_character_name_from_story(self, story_text):
        """스토리에서 주인공 이름 추출 (기본값 설정)"""
        # 간단한 이름 추출 로직 (추후 개선 가능)
        if self.favorite_topic and any(animal in self.favorite_topic.lower() for animal in ['강아지', '고양이', '토끼', '곰']):
            if '강아지' in self.favorite_topic.lower():
                return "멍멍이"
            elif '고양이' in self.favorite_topic.lower():
                return "야옹이"
            elif '토끼' in self.favorite_topic.lower():
                return "토토"
            elif '곰' in self.favorite_topic.lower():
                return "곰돌이"
        
        # 기본 이름들 중 랜덤 선택
        default_names = ["꼬마", "아이", "친구", "탐험가"]
        return default_names[0]  # 일단 첫 번째로 고정
    
    def get_story_context_summary(self, last_n_chapters=3):
        """최근 N개 챕터의 스토리 컨텍스트 요약"""
        if not self.story_context:
            return "아직 이야기가 시작되지 않았습니다."
        
        # 최근 N개 챕터만 가져오기
        recent_context = self.story_context[-last_n_chapters:] if len(self.story_context) > last_n_chapters else self.story_context
        
        summary = []
        for context in recent_context:
            chapter_info = f"챕터 {context['chapter']}: {context['content'][:100]}..."
            if context['user_input']:
                chapter_info += f" (사용자 요청: {context['user_input'][:50]}...)"
            summary.append(chapter_info)
        
        return "\n".join(summary)
    
    def add_to_story_context(self, content, user_input=None):
        """스토리 컨텍스트에 새 챕터 추가"""
        self.current_chapter += 1
        
        new_context = {
            "chapter": self.current_chapter,
            "content": content,
            "user_input": user_input,
            "learning_focus": self.learning_subject,
            "character_name": self.character_name,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.story_context.append(new_context)
        
        # 메모리 관리: 10개 이상이면 오래된 것 제거 (첫 번째는 유지)
        if len(self.story_context) > 10:
            # 첫 번째 챕터는 유지하고 중간 것들 제거
            self.story_context = [self.story_context[0]] + self.story_context[-8:]
    
    def get_character_consistency_info(self):
        """캐릭터 일관성을 위한 정보 반환"""
        return f"""
        주인공: {self.character_name}
        사용자 특성: {self.user_profile}
        좋아하는 것들: {self.favorite_topic}
        학습 주제: {self.learning_subject}
        """
    
    def get_learning_progression(self):
        """학습 진행도 추적"""
        learning_topics_covered = []
        for context in self.story_context:
            if context.get('learning_focus'):
                learning_topics_covered.append(context['learning_focus'])
        
        return {
            "main_subject": self.learning_subject,
            "chapters_count": len(self.story_context),
            "topics_covered": learning_topics_covered
        }
    
    async def generate_continuation_story(self, user_input):
        """사용자 입력을 바탕으로 연속 스토리 생성"""
        try:
            # 최근 스토리 컨텍스트 가져오기
            context_summary = self.get_story_context_summary(last_n_chapters=3)
            character_info = self.get_character_consistency_info()
            
            # 연속 스토리 생성 프롬프트
            continuation_prompt = f"""
            경계선 지능 아동을 위한 동화의 다음 장면을 만들어주세요.
            
            현재 상황:
            {context_summary}
            
            캐릭터 정보:
            {character_info}
            
            사용자 요청: {user_input}
            
            작성 가이드라인:
            1. 이전 스토리와 자연스럽게 연결되도록 작성
            2. 사용자의 요청을 창의적으로 반영
            3. 5-6세 아이가 이해할 수 있는 쉬운 언어 사용
            4. 한 문장당 10-15단어 이내로 구성
            5. {self.learning_subject} 학습 요소를 자연스럽게 포함
            6. 주인공 {self.character_name}의 특성 유지
            7. 따뜻하고 긍정적인 분위기 유지
            8. 다음 상호작용을 유도하는 열린 결말
            
            150-200자 내외의 다음 장면을 작성해주세요.
            """
            
            response = text_model.generate_content(continuation_prompt)
            return response.text
            
        except Exception as e:
            print(f"연속 스토리 생성 오류: {str(e)}")
            error_message = await self.handle_error_gracefully("api_error", str(e), "연속 스토리 생성")
            await cl.Message(content=error_message).send()
            
            return f"""
            {self.character_name}이/가 {user_input}을/를 보며 신기해했어요!
            
            "와, 정말 재미있겠다!" {self.character_name}이/가 말했어요.
            
            여러분이라면 {self.character_name}과/와 함께 무엇을 하고 싶나요?
            """
    
    def analyze_user_intent(self, user_input):
        """사용자 입력 의도 분석 (간단한 키워드 기반)"""
        user_input_lower = user_input.lower()
        
        # 감정/행동 키워드
        if any(word in user_input_lower for word in ['무서', '겁', '두려']):
            return "fear_concern"
        elif any(word in user_input_lower for word in ['기쁘', '행복', '좋아', '재미']):
            return "positive_emotion"
        elif any(word in user_input_lower for word in ['도움', '도와', '구해']):
            return "help_action"
        elif any(word in user_input_lower for word in ['만나', '친구', '같이']):
            return "social_interaction"
        elif any(word in user_input_lower for word in ['가자', '가고', '이동', '떠나']):
            return "movement_adventure"
        elif any(word in user_input_lower for word in ['배우', '공부', '알아', '학습']):
            return "learning_focus"
        else:
            return "general_continuation"
    
    async def generate_story_with_image(self, story_text, chapter_num, user_input=""):
        """스토리 텍스트와 이미지를 병렬로 생성하여 함께 반환"""
        try:
            # 이미지 생성 프롬프트 구성
            image_prompt = f"""
            Create a children's book illustration for Chapter {chapter_num}:
            
            Story content: {story_text[:200]}
            Character: {self.character_name} ({self.user_profile})
            Favorite elements: {self.favorite_topic}
            Learning subject: {self.learning_subject}
            User request context: {user_input}
            
            Style requirements:
            - Consistent character design throughout the series
            - Warm, friendly children's book illustration
            - Crayon delight style with soft textures
            - Bright, cheerful colors appropriate for 5-6 year olds
            - Simple, clear composition
            - Include elements related to {self.learning_subject}
            - Incorporate {self.favorite_topic} naturally in the scene
            
            Visual consistency: Maintain the same character appearance, proportions, and art style as previous chapters.
            """
            
            # 이미지 생성 시작 메시지
            await cl.Message(content="🎨 이미지를 생성하고 있습니다...").send()
            
            # 이미지 생성
            image_data = await self.generate_story_image(
                story_prompt=story_text,
                character_description=f"{self.character_name} ({self.user_profile})",
                style="consistent children's book crayon illustration"
            )
            
            return story_text, image_data
            
        except Exception as e:
            print(f"통합 생성 오류: {str(e)}")
            error_message = await self.handle_error_gracefully("image_generation_error", str(e), "이미지 생성")
            await cl.Message(content=error_message).send()
            return story_text, None
    
    def should_generate_image(self, chapter_num):
        """이미지 생성 여부 결정 (성능 최적화)"""
        # 첫 번째 챕터와 3챕터마다 이미지 생성
        return chapter_num == 1 or chapter_num % 3 == 0
    
    def get_progress_indicator(self):
        """진행 상황 표시기 생성"""
        total_chapters = len(self.story_context)
        progress_bar = "🟢" * min(total_chapters, 5) + "⚪" * max(0, 5 - total_chapters)
        return f"진행도: {progress_bar} ({total_chapters}/5+ 챕터)"
    
    def get_helpful_suggestions(self, user_intent="general"):
        """사용자 의도에 따른 도움말 제안"""
        suggestions = {
            "general_continuation": [
                "💡 새로운 친구를 만나게 해주세요",
                "🌟 신비한 것을 발견하게 해주세요", 
                "🎯 문제를 해결하게 해주세요"
            ],
            "learning_focus": [
                "📚 새로운 걸 배우게 해주세요",
                "🧮 문제를 풀어보게 해주세요",
                "🔍 탐험하며 발견하게 해주세요"
            ],
            "social_interaction": [
                "👫 친구와 함께 놀게 해주세요",
                "🤝 누군가를 도와주게 해주세요",
                "🎉 파티나 축제에 가게 해주세요"
            ],
            "movement_adventure": [
                "🚀 새로운 곳으로 여행하게 해주세요",
                "🏔️ 산이나 바다에 가게 해주세요",
                "🌈 마법의 문을 통과하게 해주세요"
            ]
        }
        
        return suggestions.get(user_intent, suggestions["general_continuation"])
    
    async def handle_error_gracefully(self, error_type, error_message, context=""):
        """에러를 사용자 친화적으로 처리"""
        error_responses = {
            "api_error": {
                "title": "🔧 일시적인 문제가 발생했어요",
                "message": "AI가 잠깐 쉬고 있는 것 같아요. 조금만 기다렸다가 다시 시도해주세요!",
                "suggestion": "💡 같은 내용을 다시 말씀해주시거나, 다른 방식으로 표현해보세요."
            },
            "image_generation_error": {
                "title": "🎨 이미지 만들기가 어려워요",
                "message": "그림을 그리는 중에 문제가 생겼지만, 이야기는 계속 만들 수 있어요!",
                "suggestion": "💡 텍스트로도 충분히 재미있는 이야기를 만들어갈 수 있어요."
            },
            "validation_error": {
                "title": "📝 입력값을 확인해주세요",
                "message": "입력하신 내용을 다시 한번 확인해주세요.",
                "suggestion": "💡 예시를 참고해서 다시 입력해보세요."
            },
            "context_error": {
                "title": "📚 이야기 흐름에 문제가 있어요",
                "message": "이야기 맥락을 파악하는 중에 문제가 생겼어요.",
                "suggestion": "💡 처음부터 다시 시작하거나, 간단하게 말씀해주세요."
            }
        }
        
        error_info = error_responses.get(error_type, error_responses["api_error"])
        
        response = f"{error_info['title']}\n\n"
        response += f"{error_info['message']}\n\n"
        if context:
            response += f"상황: {context}\n\n"
        response += f"{error_info['suggestion']}\n\n"
        response += "🤗 걱정하지 마세요! 함께 해결해나가요."
        
        return response
    
    def get_recovery_suggestions(self, stage):
        """단계별 복구 제안"""
        recovery_options = {
            "input_subject": [
                "🔄 '처음부터'라고 말하면 다시 시작할 수 있어요",
                "💭 '숫자', '색깔', '동물' 같은 간단한 주제를 시도해보세요"
            ],
            "input_profile": [
                "🔄 '이전 단계'라고 말하면 학습 주제부터 다시 시작해요",
                "💭 '6살', '활발함', '책 좋아함' 같이 간단히 말해보세요"
            ],
            "input_favorite": [
                "🔄 '이전 단계'라고 말하면 자기소개부터 다시 시작해요",
                "💭 '강아지', '파란색', '자동차' 같이 좋아하는 것을 말해보세요"
            ],
            "story_ongoing": [
                "🔄 '새로운 이야기'라고 말하면 처음부터 시작해요",
                "💭 간단한 단어나 짧은 문장으로 말해보세요",
                "🎲 '놀라운 일이 일어났어요'라고 말해보세요"
            ]
        }
        
        return recovery_options.get(stage, recovery_options["story_ongoing"])
    
    async def show_help_menu(self):
        """도움말 메뉴 표시"""
        help_content = """
🆘 **동화 나노바나나 도움말**

**🚀 다시 시작하기:**
• '처음부터' - 모든 것을 처음부터 다시 시작
• '이전 단계' - 바로 전 단계로 돌아가기
• '새로운 이야기' - 새로운 동화 시작

**💡 이야기 진행 팁:**
• 간단하고 명확하게 말해보세요
• '친구를 만났어요', '숲에 갔어요' 같은 표현
• 궁금한 것이나 하고 싶은 것을 자유롭게 말해보세요

**🎨 이미지 관련:**
• 첫 번째 장과 3장마다 특별한 그림이 나와요
• 이미지가 안 나와도 이야기는 계속돼요

**❓ 기타:**
• '도움말' - 이 메뉴를 다시 볼 수 있어요
• 언제든 자유롭게 대화해보세요!
        """
        
        return help_content.strip()
        
    def image_to_base64(self, image):
        """PIL 이미지를 base64로 변환"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def generate_story_image(self, story_prompt, character_description="", style="동화책 일러스트 스타일"):
        """Gemini Imagen을 사용한 실제 이미지 생성"""
        try:
            # 이미지 생성 프롬프트 작성
            image_prompt = f"""
            Create a beautiful children's book illustration:
            
            Scene: {story_prompt}
            Character: {character_description}
            Style: Cute children's book illustration, watercolor style, soft pastel colors
            
            Requirements:
            - Warm and friendly atmosphere
            - Bright, cheerful colors suitable for children
            - Simple, clear composition for young readers
            - Hand-drawn watercolor texture
            - Safe and positive content for 5-6 year olds
            - Korean children's book style
            - NO TEXT OR WORDS in the image
            - NO Korean characters or any text elements
            - Pure visual illustration without any written content
            """
            
            # Gemini 2.5 Flash Image 모델 사용 (generateContent 지원)
            imagen_model = genai.GenerativeModel('gemini-2.5-flash-image')
            
            print(f"이미지 생성 시작: {story_prompt[:50]}...")
            
            # 이미지 생성 요청
            response = imagen_model.generate_content(image_prompt)
            
            # 응답에서 이미지 데이터 추출
            if response.candidates:
                candidate = response.candidates[0]
                
                if candidate.content and candidate.content.parts:
                    for part in candidate.content.parts:
                        # 이미지 데이터가 있는지 확인
                        if hasattr(part, 'inline_data') and part.inline_data and part.inline_data.data:
                            print("✅ 이미지 생성 성공!")
                            image_data = part.inline_data.data
                            
                            # base64 디코딩이 필요한지 확인
                            if isinstance(image_data, str):
                                return base64.b64decode(image_data)
                            else:
                                return image_data
            
            print("⚠️ Imagen 응답에서 이미지 데이터를 찾을 수 없음")
            
            # 대체 방법: 이미지 생성 대신 상세한 설명 제공
            visual_description_prompt = f"""
            다음 장면을 5-6세 아이가 머릿속으로 그려볼 수 있도록 아주 구체적이고 생생하게 묘사해주세요:
            
            장면: {story_prompt}
            캐릭터: {character_description}
            
            "🎨 이런 그림을 상상해보세요!" 로 시작하는 2-3문장의 시각적 설명을 작성해주세요.
            """
            
            response = text_model.generate_content(visual_description_prompt)
            return f"🎨 {response.text}"
            
        except Exception as e:
            print(f"이미지 생성 오류: {str(e)}")
            # fallback으로 시각적 설명 제공
            visual_description_prompt = f"""
            다음 장면을 5-6세 아이가 머릿속으로 그려볼 수 있도록 아주 구체적이고 생생하게 묘사해주세요:
            
            장면: {story_prompt}
            캐릭터: {character_description}
            
            "🎨 이런 그림을 상상해보세요!" 로 시작하는 2-3문장의 시각적 설명을 작성해주세요.
            """
            
            try:
                response = text_model.generate_content(visual_description_prompt)
                return f"🎨 {response.text}"
            except:
                return f"🎨 이런 그림을 상상해보세요! {self.character_name}이/가 {story_prompt} 하는 모습을 머릿속으로 그려보세요!"
    
    def set_user_profile(self, learning_subject, character_name, favorite_topic):
        """사용자 프로필 설정"""
        self.learning_subject = learning_subject
        self.character_name = character_name  
        self.favorite_topic = favorite_topic
        self.user_profile = {
            "learning_subject": learning_subject,
            "character_name": character_name,
            "favorite_topic": favorite_topic
        }
        self.story_stage = "story1"
    
    def add_choice(self, choice):
        """사용자 선택 추가"""
        self.story_choices.append(choice)
    
    async def generate_story_text(self, prompt, context="", stage=""):
        """Gemini를 사용한 스토리 텍스트 생성"""
        try:
            profile_context = f"""
            사용자 정보:
            - 학습 주제: {self.learning_subject}
            - 주인공 이름: {self.character_name}
            - 좋아하는 주제: {self.favorite_topic}
            - 이전 선택들: {', '.join(self.story_choices) if self.story_choices else '없음'}
            """
            
            full_prompt = f"""
            당신은 경계선 지능 아동을 위한 동화 작가입니다.
            
            {profile_context}
            
            현재 단계: {stage}
            컨텍스트: {context}
            요청: {prompt}
            
            다음 가이드라인을 따라주세요:
            - 간단하고 명확한 언어 사용 (5-6세 수준)
            - 짧은 문장으로 구성 (10-15단어 이내)
            - 따뜻하고 긍정적인 톤
            - 아이들이 이해하기 쉬운 내용
            - {self.learning_subject} 학습 요소를 자연스럽게 포함
            - 주인공 이름을 {self.character_name}로 사용
            - {self.favorite_topic} 요소를 이야기에 포함
            """
            
            response = text_model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            print(f"텍스트 생성 오류: {str(e)}")
            return "죄송해요. 이야기를 만드는 중에 문제가 생겼어요. 다시 시도해주세요."
    
    async def generate_learning_question(self):
        """학습 문제 생성"""
        try:
            prompt = f"""
            {self.learning_subject}에 대한 간단한 문제를 만들어주세요.
            
            요구사항:
            - 5-6세 아이가 답할 수 있는 수준
            - 선택지 3개 (A, B, C)
            - 정답 1개 표시
            - {self.character_name}이나 {self.favorite_topic}과 연결된 내용
            
            형식:
            문제: [문제 내용]
            A) [선택지1]
            B) [선택지2] 
            C) [선택지3]
            정답: [A/B/C]
            """
            
            response = text_model.generate_content(prompt)
            result = response.text
            
            # 정답 추출
            if "정답:" in result:
                answer_line = result.split("정답:")[-1].strip()
                self.correct_answer = answer_line[0] if answer_line else "A"
            
            self.current_question = result
            return result
            
        except Exception as e:
            print(f"문제 생성 오류: {str(e)}")
            return "문제를 만드는 중 오류가 발생했어요."
    
    def check_answer(self, user_answer):
        """정답 확인"""
        user_answer = user_answer.upper().strip()
        return user_answer == self.correct_answer
    
    async def edit_story_image(self, image, edit_prompt):
        """이미진 편집 대신 새로운 이미지 생성"""
        return await self.generate_story_image(
            story_prompt=f"Previous scene modified: {edit_prompt}",
            character_description=f"{self.character_name} and friends",
            style="crayon delight 동화책 일러스트"
        )

# 전역 스토리텔러 인스턴스
storyteller = StoryTeller()

@cl.on_chat_start
async def start():
    await cl.Message(
        content="🍌 **동화 나노바나나에 오신 것을 환영합니다!** 📚✨\n\n"
        "저는 여러분만의 특별한 동화책을 만들어드리는 AI 도우미입니다.\n\n"
        "🎯 **이런 분들을 위해 만들어졌어요:**\n"
        "• 5-6세 어린이들\n"
        "• 재미있게 배우고 싶은 친구들\n"
        "• 상상력이 풍부한 모든 분들\n\n"
        "📝 **3단계로 여러분만의 동화를 만들어요:**\n"
        "┌─ **1단계**: 학습하고 싶은 주제 ➜\n"
        "├─ **2단계**: 여러분 소개 ➜\n"
        "└─ **3단계**: 좋아하는 것들 ➜ 🎉 동화 완성!\n\n"
        "**1단계 시작! 어떤 주제를 학습하고 싶으신가요?**\n"
        "💡 추천: 숫자, 색깔, 동물, 한글, 영어, 모양 등"
    ).send()
    
    # 초기 상태 설정
    storyteller.story_stage = "input_subject"

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()
    
    # 전역 명령어 처리
    if user_input.lower() in ['도움말', 'help', '도움', '헬프']:
        help_content = await storyteller.show_help_menu()
        await cl.Message(content=help_content).send()
        return
    
    elif user_input.lower() in ['처음부터', '다시시작', 'restart', '새로시작']:
        # 전체 초기화
        storyteller.__init__()
        await cl.Message(
            content="🔄 **처음부터 다시 시작합니다!**\n\n"
            "🍌 **동화 나노바나나에 다시 오신 것을 환영합니다!**\n\n"
            "**1단계 시작! 어떤 주제를 학습하고 싶으신가요?**\n"
            "💡 추천: 숫자, 색깔, 동물, 한글, 영어, 모양 등"
        ).send()
        storyteller.story_stage = "input_subject"
        return
    
    elif user_input.lower() in ['이전단계', '뒤로', 'back', '이전']:
        # 이전 단계로 복귀
        if storyteller.story_stage == "input_profile":
            storyteller.story_stage = "input_subject"
            await cl.Message(
                content="⬅️ **1단계로 돌아갑니다.**\n\n"
                "**어떤 주제를 학습하고 싶으신가요?**\n"
                "💡 추천: 숫자, 색깔, 동물, 한글, 영어, 모양 등"
            ).send()
            return
        elif storyteller.story_stage == "input_favorite":
            storyteller.story_stage = "input_profile"
            await cl.Message(
                content="⬅️ **2단계로 돌아갑니다.**\n\n"
                "**여러분에 대해 소개해주세요**\n"
                "💡 예시: '6살이고 호기심이 많아요', '조용하고 책 읽기를 좋아해요'"
            ).send()
            return
        else:
            await cl.Message(content="⚠️ 더 이상 뒤로 갈 수 없어요. '처음부터'를 입력하면 다시 시작할 수 있어요.").send()
            return
    
    # Phase 1: 사용자 정보 수집
    if storyteller.story_stage == "input_subject":
        # 1단계: 학습 주제 입력받기 - 검증 포함
        is_valid, message = storyteller.validate_input(user_input, "input_subject")
        
        if not is_valid:
            storyteller.input_attempts += 1
            if storyteller.input_attempts >= storyteller.max_attempts:
                await cl.Message(
                    content=f"❌ {message}\n\n"
                    "입력 시도 횟수를 초과했습니다. 기본값으로 '숫자'를 학습 주제로 설정하겠습니다.\n\n"
                    "**2단계: 여러분에 대해 소개해주세요**\n"
                    "나이, 성격, 특징 등을 자유롭게 알려주세요!"
                ).send()
                storyteller.learning_subject = "숫자"
                storyteller.story_stage = "input_profile"
                storyteller.reset_input_attempts()
            else:
                await cl.Message(
                    content=f"❌ {message}\n\n"
                    f"({storyteller.input_attempts}/{storyteller.max_attempts}번째 시도)\n"
                    "**다시 학습하고 싶은 주제를 알려주세요:**\n"
                    "예시: 숫자, 색깔, 동물, 한글, 영어 등"
                ).send()
        else:
            storyteller.learning_subject = user_input
            storyteller.reset_input_attempts()
            await cl.Message(
                content=f"✅ **1단계 완료!** 학습 주제: {user_input}\n\n"
                "┌─ ✅ **1단계**: 학습 주제 완료\n"
                "├─ ⏳ **2단계**: 여러분 소개 ← 지금 여기!\n"
                "└─ ⚪ **3단계**: 좋아하는 것들\n\n"
                "**2단계: 여러분에 대해 소개해주세요**\n"
                "나이, 성격, 특징 등을 자유롭게 알려주세요!\n\n"
                "💡 예시: '6살이고 호기심이 많아요', '조용하고 책 읽기를 좋아해요'"
            ).send()
            storyteller.story_stage = "input_profile"
        
    elif storyteller.story_stage == "input_profile":
        # 2단계: 사용자 프로필 입력받기 - 검증 포함
        is_valid, validation_msg = storyteller.validate_input(user_input, "input_profile")
        
        if not is_valid:
            storyteller.input_attempts += 1
            if storyteller.input_attempts >= storyteller.max_attempts:
                await cl.Message(
                    content=f"❌ {validation_msg}\n\n"
                    "입력 시도 횟수를 초과했습니다. 기본값으로 '호기심 많은 아이'로 설정하겠습니다.\n\n"
                    "**3단계: 좋아하는 것들을 알려주세요**\n"
                    "좋아하는 동물, 색깔, 음식, 놀이 등 무엇이든 좋아요!"
                ).send()
                storyteller.user_profile = "호기심 많은 아이"
                storyteller.story_stage = "input_favorite"
                storyteller.reset_input_attempts()
            else:
                await cl.Message(
                    content=f"❌ {validation_msg}\n\n"
                    f"({storyteller.input_attempts}/{storyteller.max_attempts}번째 시도)\n"
                    "**다시 여러분에 대해 소개해주세요:**\n"
                    "예시: '6살이고 호기심이 많아요', '조용하고 책 읽기를 좋아해요'"
                ).send()
        else:
            storyteller.user_profile = user_input
            storyteller.reset_input_attempts()
            await cl.Message(
                content=f"✅ **2단계 완료!** 사용자 정보: {user_input}\n\n"
                "┌─ ✅ **1단계**: 학습 주제 완료\n"
                "├─ ✅ **2단계**: 여러분 소개 완료\n"
                "└─ ⏳ **3단계**: 좋아하는 것들 ← 마지막 단계!\n\n"
                "**3단계: 좋아하는 것들을 알려주세요**\n"
                "좋아하는 동물, 색깔, 음식, 놀이 등 무엇이든 좋아요!\n\n"
                "💡 예시: '강아지와 파란색', '공주님과 성', '자동차와 로봇'"
            ).send()
            storyteller.story_stage = "input_favorite"
        
    elif storyteller.story_stage == "input_favorite":
        # 3단계: 좋아하는 것들 입력받기 - 검증 포함
        is_valid, validation_msg = storyteller.validate_input(user_input, "input_favorite")
        
        if not is_valid:
            storyteller.input_attempts += 1
            if storyteller.input_attempts >= storyteller.max_attempts:
                await cl.Message(
                    content=f"❌ {validation_msg}\n\n"
                    "입력 시도 횟수를 초과했습니다. 기본값으로 '강아지와 파란색'으로 설정하겠습니다.\n\n"
                    "🎉 **정보 수집이 완료되었습니다!**"
                ).send()
                storyteller.favorite_topic = "강아지와 파란색"
                storyteller.reset_input_attempts()
                # 정보 요약 표시로 이동
                await cl.Message(
                    content="📋 **입력하신 정보**:\n"
                    f"• **학습 주제**: {storyteller.learning_subject}\n"
                    f"• **사용자 정보**: {storyteller.user_profile}\n"
                    f"• **좋아하는 것들**: {storyteller.favorite_topic}\n\n"
                    "이제 여러분만을 위한 특별한 동화를 만들어보겠습니다! 🍌📚\n"
                    "**'동화 시작'**이라고 말하면 동화가 시작됩니다!"
                ).send()
                storyteller.story_stage = "ready_to_start"
            else:
                await cl.Message(
                    content=f"❌ {validation_msg}\n\n"
                    f"({storyteller.input_attempts}/{storyteller.max_attempts}번째 시도)\n"
                    "**다시 좋아하는 것들을 알려주세요:**\n"
                    "예시: '강아지와 파란색', '공주님과 성', '자동차와 로봇'"
                ).send()
        else:
            storyteller.favorite_topic = user_input
            storyteller.reset_input_attempts()
            
            # 모든 정보 수집 완료 - 요약 표시
            await cl.Message(
                content=f"✅ **3단계 완료!** 좋아하는 것들: {user_input}\n\n"
                "🎉 **모든 정보 수집이 완료되었습니다!**\n\n"
                "┌─ ✅ **1단계**: 학습 주제 완료\n"
                "├─ ✅ **2단계**: 여러분 소개 완료\n"
                "└─ ✅ **3단계**: 좋아하는 것들 완료\n\n"
                "📋 **여러분의 동화 재료**:\n"
                f"🎯 **학습 주제**: {storyteller.learning_subject}\n"
                f"👤 **주인공 특성**: {storyteller.user_profile}\n"
                f"💝 **특별 요소**: {storyteller.favorite_topic}\n\n"
                "🪄 **이제 마법이 시작됩니다!**\n"
                "여러분만을 위한 특별한 동화를 만들어보겠습니다! 🍌📚\n\n"
                "🚀 **'동화 시작'**이라고 말하면 모험이 시작됩니다!"
            ).send()
            storyteller.story_stage = "ready_to_start"
        
    elif storyteller.story_stage == "ready_to_start":
        # 동화 시작 준비 완료 상태
        if any(keyword in user_input.lower() for keyword in ['동화', '시작', '만들어', '스토리']):
            storyteller.story_stage = "story_generation"
            await cl.Message(content="🎨 여러분만의 특별한 동화를 만들고 있습니다... 잠시만 기다려주세요! ✨").send()
            
            # 개인 맞춤형 초기 스토리 생성
            initial_story = await storyteller.generate_initial_story()
            
            # 주인공 이름 설정
            storyteller.character_name = storyteller.extract_character_name_from_story(initial_story)
            
            # 스토리 컨텍스트에 추가 (새로운 함수 사용)
            storyteller.current_chapter = 0  # add_to_story_context에서 증가시킴
            storyteller.add_to_story_context(initial_story, user_input=None)
            storyteller.story_stage = "story_ongoing"
            
            # 첫 번째 챕터는 항상 이미지와 함께
            await cl.Message(content="🎨 첫 번째 장면을 위한 특별한 이미지를 만들고 있어요...").send()
            
            story_text, image_data = await storyteller.generate_story_with_image(
                initial_story, 
                1, 
                "story_start"
            )
            
            # 이미지가 있는 경우 이미지와 함께 표시
            if image_data and isinstance(image_data, bytes):
                # 바이너리 이미지 데이터를 파일로 저장
                image_filename = f"story_chapter_1.png"
                with open(image_filename, 'wb') as f:
                    f.write(image_data)
                
                # 이미지 요소 생성
                image_element = cl.Image(
                    name=image_filename,
                    display="inline",
                    path=image_filename
                )
                
                await cl.Message(
                    content=f"📖 **{storyteller.character_name}의 모험이 시작됩니다!**\n\n"
                    f"{initial_story}\n\n"
                    "**다음에 어떤 일이 일어났으면 좋겠나요?**\n"
                    "자유롭게 말해보세요! 여러분의 아이디어로 이야기가 계속됩니다! 🌟",
                    elements=[image_element]
                ).send()
            else:
                # 이미지 설명이나 이미지가 없는 경우
                content_message = f"📖 **{storyteller.character_name}의 모험이 시작됩니다!**\n\n"
                
                # 이미지 설명 추가
                if image_data and isinstance(image_data, str) and image_data.startswith("🎨"):
                    content_message += f"{image_data}\n\n"
                
                content_message += f"{initial_story}\n\n"
                content_message += "**다음에 어떤 일이 일어났으면 좋겠나요?**\n"
                content_message += "자유롭게 말해보세요! 여러분의 아이디어로 이야기가 계속됩니다! 🌟"
                
                await cl.Message(content=content_message).send()
        else:
            await cl.Message(
                content="**'동화 시작'**이라고 말씀해주시면 여러분만의 동화가 시작됩니다! 🍌"
            ).send()
            
    elif storyteller.story_stage == "story_ongoing":
        # 동화 진행 중 - 사용자 응답을 받아 다음 스토리 생성
        await cl.Message(content="🎨 다음 장면을 만들고 있습니다... ✨").send()
        
        # 사용자 의도 분석
        user_intent = storyteller.analyze_user_intent(user_input)
        
        # 연속 스토리 생성
        continuation_story = await storyteller.generate_continuation_story(user_input)
        
        # 스토리 컨텍스트에 추가
        storyteller.add_to_story_context(continuation_story, user_input)
        
        # 학습 진행도 확인
        learning_info = storyteller.get_learning_progression()
        
        # 의도에 따른 추가 메시지 생성
        intent_message = ""
        if user_intent == "learning_focus":
            intent_message = "📚 **학습 포인트**: 이번 장면에서 새로운 것을 배웠네요!"
        elif user_intent == "positive_emotion":
            intent_message = "😊 **기분 좋은 순간**: 즐거운 모험이 계속되고 있어요!"
        elif user_intent == "help_action":
            intent_message = "🤝 **도움주기**: 친구를 도와주는 마음이 아름다워요!"
        elif user_intent == "social_interaction":
            intent_message = "👫 **친구 만들기**: 새로운 친구와의 만남이 기대되네요!"
        
        # 이미지 생성 여부 결정
        current_chapter = learning_info['chapters_count']
        should_create_image = storyteller.should_generate_image(current_chapter)
        
        # 진행 상황 및 도움말 생성
        progress_indicator = storyteller.get_progress_indicator()
        suggestions = storyteller.get_helpful_suggestions(user_intent)
        
        if should_create_image:
            # 텍스트와 이미지를 함께 생성
            await cl.Message(content="🎨 특별한 장면을 위해 이미지도 함께 만들고 있어요...").send()
            
            story_text, image_data = await storyteller.generate_story_with_image(
                continuation_story, 
                current_chapter, 
                user_input
            )
            
            # 이미지가 있는 경우 이미지와 함께 표시
            if image_data and isinstance(image_data, bytes):
                # 바이너리 이미지 데이터를 파일로 저장
                image_filename = f"story_chapter_{current_chapter}.png"
                with open(image_filename, 'wb') as f:
                    f.write(image_data)
                
                # 이미지 요소 생성
                image_element = cl.Image(
                    name=image_filename,
                    display="inline",
                    path=image_filename
                )
                
                await cl.Message(
                    content=f"📖 **{storyteller.character_name}의 모험 - 챕터 {current_chapter}**\n\n"
                    f"{continuation_story}\n\n"
                    f"{intent_message}\n\n" if intent_message else ""
                    f"📊 **{progress_indicator}**\n\n"
                    "**또 어떤 일이 일어났으면 좋겠나요?**\n"
                    f"💡 **제안**: {' | '.join(suggestions)}\n\n"
                    "🌟 자유롭게 여러분의 아이디어를 말해주세요!",
                    elements=[image_element]
                ).send()
            else:
                # 이미지 설명이나 이미지가 없는 경우
                content_message = f"📖 **{storyteller.character_name}의 모험 - 챕터 {current_chapter}**\n\n"
                
                # 이미지 설명 추가 (있는 경우)
                if image_data and isinstance(image_data, str) and image_data.startswith("🎨"):
                    content_message += f"{image_data}\n\n"
                
                content_message += f"{continuation_story}\n\n"
                
                if intent_message:
                    content_message += f"{intent_message}\n\n"
                
                content_message += f"📊 **{progress_indicator}**\n\n"
                content_message += "**또 어떤 일이 일어났으면 좋겠나요?**\n"
                content_message += f"💡 **제안**: {' | '.join(suggestions)}\n\n"
                content_message += "🌟 자유롭게 여러분의 아이디어를 말해주세요!"
                
                await cl.Message(content=content_message).send()
        else:
            # 텍스트만 표시 (성능 최적화)
            await cl.Message(
                content=f"📖 **{storyteller.character_name}의 모험 - 챕터 {current_chapter}**\n\n"
                f"{continuation_story}\n\n"
                f"{intent_message}\n\n" if intent_message else ""
                f"📊 **{progress_indicator}**\n\n"
                "**또 어떤 일이 일어났으면 좋겠나요?**\n"
                f"💡 **제안**: {' | '.join(suggestions)}\n\n"
                "🌟 자유롭게 여러분의 아이디어를 말해주세요!"
            ).send()
            
    else:
        # 예상하지 못한 상태 - 에러 처리
        recovery_suggestions = storyteller.get_recovery_suggestions(storyteller.story_stage)
        
        await cl.Message(
            content="😅 **잠깐, 어디에 있는지 모르겠어요!**\n\n"
            "무언가 예상하지 못한 일이 일어난 것 같아요.\n\n"
            "**해결 방법:**\n" + 
            "\n".join(f"• {suggestion}" for suggestion in recovery_suggestions) + 
            "\n\n💬 또는 '도움말'을 입력해보세요!"
        ).send()

