import chainlit as cl
import google.generativeai as old_genai
from google import genai
from google.genai import types
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

# 새로운 google.genai 클라이언트 (이미지 생성용)
client = genai.Client(api_key=gemini_api_key)

# 기존 google.generativeai (텍스트 생성용)
old_genai.configure(api_key=gemini_api_key)
text_model = old_genai.GenerativeModel('gemini-2.5-flash')

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
        
    def image_to_base64(self, image):
        """PIL 이미지를 base64로 변환"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def generate_story_image(self, story_prompt, character_description="", style="동화책 일러스트 스타일"):
        """google.genai를 사용한 스트리밍 이미지 생성"""
        try:
            full_prompt = f"""
            Create a children's book illustration in crayon delight style:
            
            Scene: {story_prompt}
            Characters: {character_description}
            Style: {style}
            
            - Warm and friendly children's book illustration
            - Bright, cheerful colors
            - Hand-drawn crayon texture
            - Simple, clear composition for children
            - Cute and appealing characters
            """
            
            # 새로운 google.genai SDK 사용
            model = "gemini-2.5-flash-image"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=full_prompt),
                    ],
                ),
            ]
            
            generate_content_config = types.GenerateContentConfig(
                response_modalities=[
                    "IMAGE",
                    "TEXT",
                ],
            )

            # 스트리밍으로 이미지 생성
            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if (
                    chunk.candidates is None
                    or chunk.candidates[0].content is None
                    or chunk.candidates[0].content.parts is None
                ):
                    continue
                
                # 이미지 데이터가 있는지 확인
                if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    data_buffer = inline_data.data
                    return data_buffer  # 이미 바이너리 데이터로 반환
                else:
                    # 텍스트 응답이 오면 출력
                    if hasattr(chunk, 'text') and chunk.text:
                        print(f"모델 응답: {chunk.text}")
            
            print("이미지 생성 실패: 응답에 이미지 데이터가 없습니다.")
            return None
            
        except Exception as e:
            print(f"이미지 생성 오류: {str(e)}")
            return None
    
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
        "먼저 여러분에 대해 알려주세요! 다음 정보들을 차례대로 입력해주시면 됩니다:\n\n"
        "**1단계**: 학습하고 싶은 주제를 알려주세요\n"
        "**2단계**: 여러분에 대해 소개해주세요\n" 
        "**3단계**: 좋아하는 것들을 알려주세요\n\n"
        "**먼저, 어떤 주제를 학습하고 싶으신가요?**\n"
        "예시: 숫자, 색깔, 동물, 한글, 영어 등"
    ).send()
    
    # 초기 상태 설정
    storyteller.story_stage = "input_subject"

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.strip()
    
    # Phase 1: 사용자 정보 수집
    if storyteller.story_stage == "input_subject":
        # 1단계: 학습 주제 입력받기
        storyteller.learning_subject = user_input
        await cl.Message(
            content=f"✅ **학습 주제**: {user_input}\n\n"
            "**2단계: 여러분에 대해 소개해주세요**\n"
            "나이, 성격, 특징 등을 자유롭게 알려주세요!\n\n"
            "예시: '6살이고 호기심이 많아요', '조용하고 책 읽기를 좋아해요'"
        ).send()
        storyteller.story_stage = "input_profile"
        
    elif storyteller.story_stage == "input_profile":
        # 2단계: 사용자 프로필 입력받기
        storyteller.user_profile = user_input
        await cl.Message(
            content=f"✅ **사용자 정보**: {user_input}\n\n"
            "**3단계: 좋아하는 것들을 알려주세요**\n"
            "좋아하는 동물, 색깔, 음식, 놀이 등 무엇이든 좋아요!\n\n"
            "예시: '강아지와 파란색', '공주님과 성', '자동차와 로봇'"
        ).send()
        storyteller.story_stage = "input_favorite"
        
    elif storyteller.story_stage == "input_favorite":
        # 3단계: 좋아하는 것들 입력받기
        storyteller.favorite_topic = user_input
        
        # 모든 정보 수집 완료 - 요약 표시
        await cl.Message(
            content=f"✅ **좋아하는 것들**: {user_input}\n\n"
            "🎉 **정보 수집이 완료되었습니다!**\n\n"
            "📋 **입력하신 정보**:\n"
            f"• **학습 주제**: {storyteller.learning_subject}\n"
            f"• **사용자 정보**: {storyteller.user_profile}\n"
            f"• **좋아하는 것들**: {storyteller.favorite_topic}\n\n"
            "이제 여러분만을 위한 특별한 동화를 만들어보겠습니다! 🍌📚\n"
            "**'동화 시작'**이라고 말하면 동화가 시작됩니다!"
        ).send()
        storyteller.story_stage = "ready_to_start"
        
    elif storyteller.story_stage == "ready_to_start":
        # 동화 시작 준비 완료 상태
        if any(keyword in user_input.lower() for keyword in ['동화', '시작', '만들어', '스토리']):
            storyteller.story_stage = "story_generation"
            await cl.Message(content="🎨 여러분만의 특별한 동화를 만들고 있습니다... 잠시만 기다려주세요! ✨").send()
            
            # 개인 맞춤형 스토리 생성 (이후 구현 예정)
            await cl.Message(content="🚧 **다음 단계에서 구현 예정**: 맞춤형 스토리 생성 기능").send()
        else:
            await cl.Message(
                content="**'동화 시작'**이라고 말씀해주시면 여러분만의 동화가 시작됩니다! 🍌"
            ).send()
            
    else:
        # 기존 동화 진행 로직 (추후 개선 예정)
        await cl.Message(content="🚧 **개발 중**: 동화 진행 기능이 곧 추가될 예정입니다!").send()

