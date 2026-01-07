import ollama
import os
from typing import List


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
    
    def _build_prompt(
        self,
        job_description: str,
        job_title: str,
        company: str,
        requirements: List[str],
        user_name: str,
        user_skills: str,
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
