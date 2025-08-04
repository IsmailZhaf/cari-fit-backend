import asyncio
import time
import hashlib
from urllib.parse import quote_plus
from crawl4ai import AsyncWebCrawler
from core.ai.crawl import client, JobList, Jobs
from huey.contrib.djhuey import periodic_task
from huey import crontab
from asgiref.sync import sync_to_async
from datetime import datetime
from core.ai.chromadb import chroma_client, embedding_function
from jobs.utils import save_job, sanitize_collection_name



import logging

# Konfigurasi dasar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()  # agar tetap muncul di terminal
    ]
)

logger = logging.getLogger(__name__)

logger.info(time.tzname)        # Nama timezone lokal (misal: ('WIB', 'WIB'))
logger.info(time.timezone)      # Offset dalam detik dari UTC (negatif kalau di depan UTC)



MAX_JOBS_PER_KEYWORD = 5  # max job per kategori

CATEGORY_KEYWORDS = {
    "Teknologi ": [
        "software engineer", "devops engineer", "data scientist",
        "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    ],
    # "Bisnis dan Manajemen": [
    #     "business analyst", "project manager", "product manager",
    #     "hr specialist", "recruiter", "marketing specialist", "digital marketing",
    #     "finance analyst", "accountant"
    # ],
    # "Kreatif": [
    #     "graphic designer", "ui designer", "content writer", "copywriter",
    #     "video editor", "social media specialist", "brand strategist"
    # ],
    # "Manufaktur": [
    #     "mechanical engineer", "industrial engineer", "supply chain analyst",
    #     "procurement specialist", "quality assurance engineer", "qa manufaktur", "qa logistik"
    # ]
}


@periodic_task(crontab(hour=7, minute=37), name="crawl_jobs") # 12-00 dikurangi 7 jam
def crawl_jobs():
    try:
        asyncio.run(crawl_jobs_async())
    except Exception as e:
        logger.info(f"Error running crawl_jobs: {e}")


def generate_md5_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

async def fetch_with_retry(crawler, url, retries=2):
    for attempt in range(retries + 1):
        try:
            return await crawler.arun(url)
        except Exception as e:
            if attempt == retries:
                raise
            logger.info(f"🔁 Retry {attempt+1} for {url} due to error: {e}")
            await asyncio.sleep(2)  # jeda sebelum retry


async def crawl_jobs_by_keywords(crawler, category, keywords, max_jobs_per_keyword):
    logger.info(f"\n📁 Crawling category: {category.upper()}")
    collected_jobs = []

    for keyword in keywords:
        keyword_jobs = []
        logger.info(f"🔍 Crawling keyword: {keyword}")

        base_url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(keyword)}&location=Indonesia&start={{start}}"
        urls = [base_url.format(start=i) for i in range(0, 25, 25)]  # hanya 1 halaman

        for idx, url in enumerate(urls):
            if len(keyword_jobs) >= max_jobs_per_keyword:
                break

            logger.info(f"🌐 Crawling '{keyword}' - Page {idx + 1}")
            try:
                result = await crawler.arun(url)
                await asyncio.sleep(1)  # delay 1 detik setelah crawl tiap halaman  

                if not result.markdown.strip():
                    logger.info(f"🛑 No content on page {idx + 1}, skipping.")
                    continue

                res = client.beta.chat.completions.parse(
                    model='gpt-4o-mini',
                    messages=[
                        {"role": "system", "content": "Extract job list from the given text"},
                        {"role": "user", "content": result.markdown},
                    ],
                    response_format=JobList,
                )

                parsed = res.choices[0].message.parsed
                logger.info(f"  ✅ Found {len(parsed.jobs)} jobs on page {idx + 1}")

                remaining = max_jobs_per_keyword - len(keyword_jobs)
                keyword_jobs.extend(parsed.jobs[:remaining])

            except Exception as e:
                logger.info(f"  ❌ Failed to crawl page {idx + 1}: {e}")

        logger.info(f"  ✅ Collected {len(keyword_jobs)} jobs for keyword '{keyword}'")

        collection_name = sanitize_collection_name(f"jobs_{category}")
        collection = chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function
        )


        for idx, job in enumerate(keyword_jobs, start=1):
            try:
                logger.info(f"\n➡️ Processing job {idx}: {job.job_title} at {job.company_name}")

                result = await crawler.arun(job.url)

                res = client.beta.chat.completions.parse(
                    model='gpt-4o-mini',
                    messages=[
                        {"role": "system", "content": "Extract job detail from the given text"},
                        {"role": "user", "content": result.markdown},
                    ],
                    response_format=Jobs,
                )

                job_data = res.choices[0].message.parsed
                job_json = job_data.model_dump()
                job_json['category'] = category
                logger.info("  ✅ Job data parsed successfully.")
                logger.info(f"Job data: {job_json}")

                job_instance = await sync_to_async(save_job)(job_json)
                job_id = str(job_instance.id)
                logger.info(f"  ✅ Job '{job.job_title}' saved to DB.")

                # ⬇️ Tambahkan ke Chroma langsung
                try:
                    document = {
                        "job_id": job_id,
                        "category": job_json["category"],
                        "company_name": job_json["company_name"],
                        "job_description": job_json["job_description"],
                        "job_title": job_json["job_title"],
                        "job_type": job_json["job_type"],
                        "education_level": job_json["education_level"],
                        "experience_level": job_json["experience_level"],
                        "skills_required": job_json["skills_required"],
                        "salary": job_json["salary"],
                        "date_posted": job_json["date_posted"],
                    }

                    metadata = {
                        "job_id": job_id,
                        "job_title": job_json["job_title"],
                        "company_name": job_json["company_name"],
                    }

                    existing_data = collection.get(ids=[job_id])
                    if existing_data and existing_data.get("ids"):
                        collection.delete(ids=[job_id])

                    collection.add(
                        ids=[job_id],
                        metadatas=[metadata],
                        documents=[str(document)],
                    )
                    logger.info(f"  ✅ Uploaded job '{job.job_title}' to ChromaDB.")
                except Exception as e:
                    logger.info(f"  ❌ Failed to upload job '{job.job_title}' to ChromaDB: {e}")

            except Exception as e:
                logger.info(f"❌ Error processing job '{job.job_title}': {e}")
        logger.info(f"🕒 Sleeping 2s after keyword '{keyword}'")
        await asyncio.sleep(2)

    return collected_jobs

async def crawl_and_upload_category(crawler, category, keywords):
    try:
        await crawl_jobs_by_keywords(crawler, category, keywords, MAX_JOBS_PER_KEYWORD)
    except Exception as e:
        logger.info(f"❌ Error during crawling/uploading category {category}: {e}")



async def crawl_jobs_async():
    start_time = time.time()
    logger.info(f"[{datetime.now()}] crawl_jobs_async running...")

    async with AsyncWebCrawler() as crawler:
        tasks = [
            crawl_and_upload_category(crawler, category, keywords)
            for category, keywords in CATEGORY_KEYWORDS.items()
        ]
        await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    logger.info(f"\n⏱️ Total waktu crawling dan upload: {int(elapsed // 60)} menit {int(elapsed % 60)} detik")

