import chainlit as cl
import google.generativeai as genai
import os
import base64
from PIL import Image
import io
from dotenv import load_dotenv
import asyncio

# 환경변수 로드
load_dotenv()

# API 키 설정
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash-image')

class StoryTeller:
    def __init__(self):
        self.story_context = []
        self.current_chapter = 0
        
    def image_to_base64(self, image):
        """PIL 이미지를 base64로 변환"""
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
    
    async def generate_story_image(self, story_prompt, character_description="", style="동화책 일러스트 스타일"):
        """스토리와 캐릭터 설명을 기반으로 이미지 생성"""
        try:
            full_prompt = f"""
            {style}로 그려주세요.
            
            스토리 상황: {story_prompt}
            캐릭터 설명: {character_description}
            
            따뜻하고 친근한 동화책 일러스트로 그려주세요. 
            선명하고 밝은 색상을 사용하고, 아이들이 좋아할만한 귀여운 스타일로 만들어주세요.
            """
            
            response = model.generate_content([full_prompt])
            
            if response.parts and response.parts[0].inline_data:
                generated_img_data = response.parts[0].inline_data.data
                return base64.b64decode(generated_img_data)
            return None
            
        except Exception as e:
            print(f"이미지 생성 오류: {str(e)}")
            return None
    
    async def edit_story_image(self, image, edit_prompt):
        """기존 이미지를 편집"""
        try:
            img_data = self.image_to_base64(image)
            
            response = model.generate_content([
                {
                    'inline_data': {
                        'mime_type': 'image/png',
                        'data': img_data
                    }
                },
                f"동화책 일러스트 스타일을 유지하면서 다음과 같이 편집해주세요: {edit_prompt}"
            ])
            
            if response.parts and response.parts[0].inline_data:
                generated_img_data = response.parts[0].inline_data.data
                return base64.b64decode(generated_img_data)
            return None
            
        except Exception as e:
            print(f"이미지 편집 오류: {str(e)}")
            return None

# 전역 스토리텔러 인스턴스
storyteller = StoryTeller()

@cl.on_chat_start
async def start():
    await cl.Message(
        content="🍌 **동화 나노바나나에 오신 것을 환영합니다!** 📚✨\n\n"
        "저는 여러분만의 특별한 동화책을 만들어드리는 AI 도우미입니다.\n\n"
        "**어떤 동화를 만들고 싶으세요?**\n"
        "- 주인공과 배경을 알려주세요\n"
        "- 어떤 모험을 떠나고 싶은지 말해주세요\n"
        "- 이미지도 함께 생성해드립니다!\n\n"
        "예시: '용감한 토끼가 마법의 숲에서 친구들을 구하는 이야기를 만들어주세요'"
    ).send()

@cl.on_message
async def main(message: cl.Message):
    user_input = message.content.lower()
    
    # 새로운 동화 시작
    if any(keyword in user_input for keyword in ['동화', '이야기', '스토리', '만들어']):
        await cl.Message(content="🎨 동화 이미지를 생성하고 있습니다... 잠시만 기다려주세요!").send()
        
        # 이미지 생성
        image_data = await storyteller.generate_story_image(
            story_prompt=message.content,
            character_description="귀여운 동화 캐릭터들",
            style="따뜻하고 부드러운 동화책 일러스트"
        )
        
        if image_data:
            # 이미지를 파일로 저장
            image_filename = f"story_image_{storyteller.current_chapter}.png"
            with open(image_filename, 'wb') as f:
                f.write(image_data)
            
            # 이미지 요소 생성
            image_element = cl.Image(
                name=image_filename,
                display="inline",
                path=image_filename
            )
            
            # 스토리 텍스트 생성
            story_response = f"""
📖 **새로운 동화가 시작됩니다!**

{message.content}

🎨 위의 이미지가 여러분의 이야기를 표현하고 있습니다!

**다음에 어떤 일이 일어났으면 좋겠나요?**
- 이야기를 계속 이어가거나
- 이미지를 수정하고 싶다면 말해주세요
- "이미지 편집: [원하는 변경사항]" 형식으로 요청해주세요

예시: "이미지 편집: 배경을 밤하늘로 바꿔주세요" 또는 "토끼가 더 큰 모험을 떠났어요"
            """
            
            await cl.Message(
                content=story_response,
                elements=[image_element]
            ).send()
            
            storyteller.current_chapter += 1
        else:
            await cl.Message(content="죄송합니다. 이미지 생성에 실패했습니다. 다시 시도해주세요.").send()
    
    # 이미지 편집 요청
    elif '이미지 편집' in user_input or '편집' in user_input:
        # 가장 최근 이미지 파일 찾기
        latest_image = f"story_image_{storyteller.current_chapter-1}.png"
        
        if os.path.exists(latest_image):
            await cl.Message(content="🎨 이미지를 편집하고 있습니다...").send()
            
            # 편집 프롬프트 추출
            edit_prompt = message.content.replace('이미지 편집:', '').replace('편집:', '').strip()
            
            # 이미지 로드
            with Image.open(latest_image) as img:
                edited_image_data = await storyteller.edit_story_image(img, edit_prompt)
            
            if edited_image_data:
                # 편집된 이미지 저장
                edited_filename = f"story_image_{storyteller.current_chapter}_edited.png"
                with open(edited_filename, 'wb') as f:
                    f.write(edited_image_data)
                
                image_element = cl.Image(
                    name=edited_filename,
                    display="inline", 
                    path=edited_filename
                )
                
                await cl.Message(
                    content=f"✨ **이미지가 편집되었습니다!**\n\n편집 내용: {edit_prompt}\n\n계속해서 이야기를 이어가거나 추가 편집을 요청해주세요!",
                    elements=[image_element]
                ).send()
                
                storyteller.current_chapter += 1
            else:
                await cl.Message(content="이미지 편집에 실패했습니다. 다시 시도해주세요.").send()
        else:
            await cl.Message(content="편집할 이미지를 찾을 수 없습니다. 먼저 동화를 시작해주세요!").send()
    
    # 스토리 계속하기
    else:
        await cl.Message(content="🎨 다음 장면을 생성하고 있습니다...").send()
        
        # 다음 장면 이미지 생성
        image_data = await storyteller.generate_story_image(
            story_prompt=f"이전 이야기의 다음 장면: {message.content}",
            character_description="동일한 캐릭터들",
            style="일관된 동화책 일러스트 스타일"
        )
        
        if image_data:
            image_filename = f"story_image_{storyteller.current_chapter}.png"
            with open(image_filename, 'wb') as f:
                f.write(image_data)
            
            image_element = cl.Image(
                name=image_filename,
                display="inline",
                path=image_filename
            )
            
            story_continue = f"""
📖 **이야기가 계속됩니다...**

{message.content}

🎨 새로운 장면이 펼쳐집니다!

**또 어떤 재미있는 일이 일어날까요?** 계속 이야기를 들려주세요!
            """
            
            await cl.Message(
                content=story_continue,
                elements=[image_element]
            ).send()
            
            storyteller.current_chapter += 1
        else:
            await cl.Message(content="이미지 생성에 실패했습니다. 텍스트로 이야기를 계속해주세요!").send()

if __name__ == "__main__":
    cl.run()