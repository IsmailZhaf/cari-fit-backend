from openai import OpenAI
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

client = OpenAI(
    api_key= os.environ.get("OPENAI_API_KEY"),
)



class Jobs(BaseModel):
    job_id: str = Field(default="Not specified", description="The unique identifier for the job")
    job_title: str = Field(default="Not specified", description="The title of the job")
    job_description: str = Field(default="Not specified", description="The description of the job")
    company_name: str = Field(default="Not specified", description="The name of the company")
    company_desc: str = Field(default="Not specified", description="The description of the company")
    company_logo: str = Field(default="Not specified", description="The **URL to the company logo** scraped by Crawl4AI")
    company_size: str = Field(default="Not specified", description="The size of employee in the company")
    location: str = Field(default="Not specified", description="The location of the job")
    salary: str = Field(default="Not specified", description="The salary of the job")
    date_posted: str = Field(default="Not specified", description="The date the job was posted")
    url: str = Field(default="Not specified", description="The **apply button link** scraped by Crawl4AI")
    job_type: str = Field(default="Not specified", description="The type of job, e.g. full-time, part-time")
    industry: str = Field(default="Not specified", description="The industry the job belongs to")
    experience_level: str = Field(default="Not specified", description="The experience level required for the job")
    education_level: str = Field(default="Not specified", description="The education level required for the job")
    skills_required: List[str] = Field(default_factory=list, description="The skills required for the job")


class JobList(BaseModel):
    jobs: list[Jobs]