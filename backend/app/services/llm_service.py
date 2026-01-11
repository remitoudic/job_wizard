import ollama
import os
import json
from typing import List, Dict


class LLMService:
    """Service for generating cover letters using Ollama LLM"""
    
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
        
        # Configure ollama client
        self.client = ollama.Client(host=self.host)
    
    async def generate_cover_letter(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: List[str],
        user_name: str = "Applicant",
        user_skills: str = "",
        context_text: str = None,
    ) -> str:
        """
        Generate a personalized cover letter
        
        Args:
            job_description: Full job description text
            job_title: Job title
            company: Company name
            requirements: List of job requirements
            user_name: Applicant's name
            user_skills: Applicant's skills/experience (optional)
            context_text: Additional context from uploaded PDF (optional)
            
        Returns:
            Generated cover letter text
        """
        # Build the prompt
        prompt = self._build_prompt(
            job_description=job_description,
            job_title=job_title,
            company=company,
            requirements=requirements,
            user_name=user_name,
            user_skills=user_skills,
            context_text=context_text,
        )
        
        # Generate using Ollama
        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 1000,
                }
            )
            
            cover_letter = response['response'].strip()
            return cover_letter
            
        except Exception as e:
            raise Exception(f"Failed to generate cover letter with Ollama: {str(e)}")

    async def extract_contact_info(self, context_text: str) -> Dict[str, str]:
        """
        Extract contact info from context text using LLM
        """
        prompt = f"""You are a data extraction assistant. Extract contact information from the following text.
        
Text:
{context_text[:2000]}

Instructions:
1. Extract Email, Phone Number, and LinkedIn/Website URL (if present).
2. Return ONLY a JSON object with keys: "email", "phone", "linkedin".
3. If a field is not found, use an empty string.
4. Do not include any other text.

JSON Extract:"""

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                format="json",  
                options={
                    "temperature": 0.1, 
                }
            )
            
            response_text = response['response'].strip()
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif response_text.startswith("```"):
                response_text = response_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
            return {"email": "", "phone": "", "linkedin": ""}

    def _build_prompt(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: List[str],
        user_name: str,
        user_skills: str,
        context_text: str = None,
    ) -> str:
        """Build the prompt for the LLM"""
        
        requirements_text = "\n".join(f"- {req}" for req in requirements[:5])
        
        prompt = f"""You are a professional cover letter writer. Write a compelling, personalized cover letter for the following job application.

Job Title: {job_title}
Company: {company}

Job Requirements:
{requirements_text}

Job Description:
{job_description[:1000]}

Applicant Name: {user_name}
{f"Applicant Skills/Experience: {user_skills}" if user_skills else ""}
{f"Additional Applicant Context (CV/Cover Letter info): {context_text}" if context_text else ""}

Instructions:
1. Write a professional cover letter (3-4 paragraphs)
2. Express enthusiasm for the role and company
3. Highlight how the applicant's skills match the job requirements
4. Keep it concise and impactful (250-350 words)
5. Use a professional but warm tone
6. Do NOT include the applicant's address or contact information
7. Do NOT include the date
8. Start with "Dear Hiring Manager,"

Cover Letter:"""

        return prompt
