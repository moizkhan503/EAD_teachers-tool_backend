"""
Service for generating lesson plans using Groq.
"""
import logging
from typing import List, Dict, Any, Optional
import os
import json
from groq import Groq
from app.config import settings
from app.models import LessonPlanRequest, LessonPlanResponse, LessonPlanUnit

logger = logging.getLogger(__name__)

class LessonPlanGenerator:
    """Service for generating lesson plans using Groq."""
    
    def __init__(self):
        """Initialize the Groq client with model from config."""
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL  # Using model from config
        
    def _generate_prompt(self, request: LessonPlanRequest) -> str:
        """Generate the prompt for Groq based on the request."""
        return f"""
        You are an expert curriculum designer. Create a detailed lesson plan based on the following requirements:
        
        SYLLABUS CONTENT:
        {request.syllabus_data}
        
        Create {request.num_classes} lesson plans. Each lesson should be {request.class_duration} long.
        
        TEACHING STYLE: {request.teaching_style.capitalize()}
        HOMEWORK PREFERENCE: {request.homework_preference.capitalize()}
        
        For each lesson plan, include:
        1. A clear title
        2. 3-5 learning objectives
        3. 3-5 engaging activities that match the teaching style
        4. Required resources/materials
        5. Homework assignment (if applicable)
        
        Format the response as a JSON object with the following structure:
        {{
            "lesson_plans": [
                {{
                    "title": "Lesson Title",
                    "objectives": ["objective 1", "objective 2", ...],
                    "activities": ["activity 1", "activity 2", ...],
                    "resources": ["resource 1", "resource 2", ...],
                    "homework": "Homework description"
                }}
            ]
        }}
        """
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the Groq response into a structured format."""
        try:
            # Extract JSON from markdown code block if present
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Groq response: {e}")
            raise ValueError("Failed to generate valid lesson plan. Please try again.")
    
    async def generate_lesson_plans(self, request: LessonPlanRequest) -> LessonPlanResponse:
        """
        Generate lesson plans using Groq based on the provided request.
        
        Args:
            request: LessonPlanRequest containing syllabus and preferences
            
        Returns:
            LessonPlanResponse containing the generated lesson plans
            
        Raises:
            ValueError: If there's an error generating the lesson plans
            ConnectionError: If there's a connection issue with the Groq API
        """
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY is not set in environment variables")
            raise ConnectionError("Service configuration error. Please check server logs.")
            
        try:
            prompt = self._generate_prompt(request)
            
            # Call Groq API with timeout and better error handling
            try:
                completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful teaching assistant that creates detailed, engaging lesson plans."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=4000,
                    top_p=1,
                    response_format={"type": "json_object"},
                    timeout=30.0  # 30 seconds timeout
                )
            except Exception as e:
                logger.error(f"Groq API connection error: {str(e)}")
                raise ConnectionError("Unable to connect to the lesson planning service. Please try again later.") from e
            
            # Extract and parse the response
            response_content = completion.choices[0].message.content
            parsed_response = self._parse_response(response_content)
            
            # Convert to Pydantic models
            lesson_plans = [
                LessonPlanUnit(
                    title=lesson.get("title", f"Lesson {i+1}"),
                    objectives=lesson.get("objectives", []),
                    activities=lesson.get("activities", []),
                    resources=lesson.get("resources", []),
                    homework=lesson.get("homework"),
                    duration=request.class_duration
                )
                for i, lesson in enumerate(parsed_response.get("lesson_plans", []))
            ]
            
            # Calculate total duration
            total_minutes = len(lesson_plans) * int(request.class_duration.split()[0])
            hours = total_minutes // 60
            minutes = total_minutes % 60
            total_duration = f"{hours} hours {minutes} minutes" if hours > 0 else f"{minutes} minutes"
            
            return LessonPlanResponse(
                success=True,
                lesson_plans=lesson_plans,
                total_duration=total_duration,
                teaching_style=request.teaching_style
            )
            
        except Exception as e:
            logger.error(f"Error generating lesson plans: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to generate lesson plans: {str(e)}")

# Create a singleton instance
lesson_plan_generator = LessonPlanGenerator()

# Export the main function
async def generate_lesson_plans(request: LessonPlanRequest) -> LessonPlanResponse:
    """Generate lesson plans using the singleton instance."""
    return await lesson_plan_generator.generate_lesson_plans(request)
