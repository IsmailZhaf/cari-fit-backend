import re
from .models import Job
from core.ai.chromadb import chroma_client, embedding_function
from datetime import datetime

def sanitize_collection_name(name: str) -> str:
    """
    Sanitize category name to be a valid ChromaDB collection name:
    - Replace all non-alphanumeric characters with underscores
    - Strip leading/trailing underscores
    - Ensure length between 3 and 512
    """
    # Lowercase and replace non-alphanumeric characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', name.lower())
    sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
    sanitized = sanitized.strip('_')

    # Ensure name starts and ends with alphanumeric character
    if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', sanitized):
        raise ValueError(f"Invalid sanitized name: {sanitized}")

    # Validate length
    if len(sanitized) < 3 or len(sanitized) > 512:
        raise ValueError(f"Collection name must be 3-512 characters: {sanitized}")

    return sanitized

# def get_collection_and_delete_by_category(category_name: str):
#     collection_name = sanitize_collection_name(f"jobs_{category_name}")

#     # Ambil nama-nama collection yang sudah ada
#     existing_collections = [col.name for col in chroma_client.list_collections()]

#     if collection_name in existing_collections:
#         chroma_client.delete_collection(name=collection_name)

#     return chroma_client.get_or_create_collection(
#         name=collection_name,
#         embedding_function=embedding_function
#     )

def get_collection_by_category(category_name: str):
    collection_name = sanitize_collection_name(f"jobs_{category_name}")

    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function
    )


def save_job(job_json: dict) -> Job:
    job, created = Job.objects.update_or_create(
        url=job_json.get("url"),
        defaults={
            "category": job_json.get("category"),
            "job_title": job_json.get("job_title"),
            "company_name": job_json.get("company_name"),
            "company_industry": job_json.get("industry"),
            "company_employee_size": job_json.get("company_size"),
            "company_desc": job_json.get("company_desc"),
            "location": job_json.get("location"),
            "url": job_json.get("url"),
            "job_type": job_json.get("job_type"),
            "experience_level": job_json.get("experience_level"),
            "education_level": job_json.get("education_level"),
            "skills_required": job_json.get("skills_required"),
            "salary": job_json.get("salary"),
            "date_posted": job_json.get("date_posted"),
            "job_description": job_json.get("job_description"),
            "uploaded_to_vector_db": False,
        }
    )
    return job

def get_jobs_not_uploaded():
    return list(Job.objects.filter(uploaded_to_vector_db=False))


def mark_job_uploaded(job_id: int):
    Job.objects.filter(id=job_id).update(uploaded_to_vector_db=True)
