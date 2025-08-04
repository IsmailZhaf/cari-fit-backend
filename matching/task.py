import os
from huey.contrib.djhuey import task
from dotenv import load_dotenv
from django.db import transaction
from cv.models import CV
from core.ai.pm import PromptManager
from matching.models import JobRecommendation 
from jobs.models import Job  # import model Job
from jobs.utils import get_collection_by_category
from pydantic import BaseModel, Field
from typing import List, Literal
from django.utils import timezone
from datetime import date
from notifications.methods import send_notification
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Tambahkan handler log ke file jika belum
handler = logging.FileHandler("job_matching.log")
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)



load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MatchedJob(BaseModel):
    job_id: str = Field(..., description="ID unik untuk pekerjaan ini")
    title: str = Field(..., description="Judul pekerjaan")
    company: str = Field(..., description="Nama perusahaan")
    location: str = Field(..., description="Lokasi pekerjaan")
    
    match_score: float = Field(..., ge=0, le=100, description="Skor kecocokan antara 0–100%")
    matched_skills: List[str] = Field(..., description="Daftar keterampilan yang cocok antara CV dan pekerjaan")
    required_skills: List[str] = Field(..., description="Daftar keterampilan yang dibutuhkan oleh pekerjaan")
    
    job_description: str = Field(..., description="Deskripsi pekerjaan")
    reason: str = Field(..., description="Alasan kenapa pekerjaan ini cocok dengan kandidat")
    
    job_type: str = Field(..., description="Jenis pekerjaan, misalnya full-time, part-time")
    industry: str = Field(..., description="Industri tempat pekerjaan ini berada")
    experience_level: str = Field(..., description="Tingkat pengalaman yang dibutuhkan")
    education_level: str = Field(..., description="Tingkat pendidikan minimum yang dibutuhkan")
    
    skills_required: str = Field(..., description="Kumpulan semua skill yang dibutuhkan (dalam format string)")
    date_posted: date = Field(..., description="Tanggal lowongan ini dipublikasikan")

class MatchingJob(BaseModel):
    jobs: List[MatchedJob] = Field(..., description="Daftar pekerjaan yang cocok berdasarkan analisis pencocokan")


CATEGORY_KEYWORDS = {
    "Teknologi": [
        "software engineer", "devops engineer", "data scientist",
        "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    ],
    "Bisnis dan Manajemen": [
        "business analyst", "project manager", "product manager",
        "hr specialist", "recruiter", "marketing specialist", "digital marketing",
        "finance analyst", "accountant"
    ],
    "Kreatif": [
        "graphic designer", "ui designer", "content writer", "copywriter",
        "video editor", "social media specialist", "brand strategist"
    ],
    "Industri dan Manufaktur": [
        "mechanical engineer", "industrial engineer", "supply chain analyst",
        "procurement specialist", "quality assurance engineer", "qa manufaktur", "qa logistik"
    ]
}

CategoryLiteral = Literal["Teknologi", "Bisnis dan Manajemen", "Kreatif", "Industri dan Manufaktur", "None"]


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


@task()
def job_matching(user, cv_id, skills, experience):
    JobRecommendation.objects.filter(user=user).delete()
    send_notification({
    "type": "info",
    "title": "🔎 Proses Pencocokan Dimulai",
    "message": "Kami sedang menganalisis CV Anda dan mencari lowongan pekerjaan yang paling sesuai..."
    })

    cv = CV.objects.filter(id=cv_id).first()
    if not cv:
        logger.info(f"CV dengan id {cv_id} tidak ditemukan.")
        send_notification({
            "type": "error",
            "title": "❌ CV Tidak Ditemukan",
            "message": "Kami tidak dapat menemukan CV yang Anda unggah. Silakan coba unggah kembali."
        })
        return

    parsed_cv = cv.parsed_text
    # result = analyze_cv(parsed_cv)
    category = cv.category
    logger.info(f'Skill yang dianalisis: {skills}')
    logger.info(f'Pengalaman yang dianalisis: {experience}')
    logger.info(f"Kategori pekerjaan yang dianalisis: {category}")
    send_notification({
    "type": "info",
    "title": "🧠 CV Telah Dianalisis",
    "message": f"Profil Anda paling cocok untuk pekerjaan di bidang '{category}'. Sedang mengambil daftar lowongan yang sesuai..."
    })

    try:
        with transaction.atomic():
            JobRecommendation.objects.filter(user=user).delete()
            logger.info(f"✅ Semua rekomendasi lama untuk user {user.username} telah dihapus.")

        collection = get_collection_by_category(category)
        logger.info("Total jobs in collection: %s", collection.count())
        send_notification({
            "type": "info",
            "title": "📂 Mengambil Data Lowongan",
            "message": f"Ditemukan lowongan di bidang '{category}'. Memulai proses pencocokan..."
        })


        result = collection.query(
            query_texts=[parsed_cv],
            n_results=30,
            include=["documents", "distances", "metadatas"],
        )

        documents = result.get("documents", [[]])[0]
        logger.info(f"Total documents returned: {len(documents)}")
        for i, doc in enumerate(documents, 1):
            logger.info(f"Lowongan {i}:\n{doc.strip()}\n\n")
        all_matched_jobs = []

        for batch_index, docs_batch in enumerate(chunked(documents, 10), 1):
            formatted_jobs = "".join([f"Lowongan {i+1}:{doc.strip()}\n\n" for i, doc in enumerate(docs_batch)])

            pm_batch = PromptManager()
            pm_batch.add_message("system", f"""
                    # 🎯 Spesialis AI Pencocokan Lowongan — Prompt Penilaian & Peringkat

                    Kamu adalah mesin pencocokan kerja bertenaga AI yang sangat cerdas dan dirancang untuk mengevaluasi profil kandidat serta memberikan **rekomendasi pekerjaan yang diperingkatkan**. Keputusanmu harus berdasarkan kerangka penilaian terstruktur dengan **alasan kuantitatif**, **kecocokan keterampilan**, dan **waktu publikasi lowongan**.

                    ## 🔎 KERANGKA PENILAIAN

                    ### Dimensi Penilaian Utama (Total: 100%)
                    - **Kecocokan Keterampilan Teknis (30%)**: Kesesuaian antara keterampilan yang dimiliki dengan yang dibutuhkan (tools, tech stack, bahasa pemrograman).
                    - **Relevansi Pengalaman (25%)**: Kemiripan dengan peran, tanggung jawab, dan domain proyek sebelumnya.
                    - **Kesesuaian Pendidikan (10%)**: Tingkat pendidikan dan jurusan yang sesuai.
                    - **Waktu Publikasi Lowongan (15%)**: Berdasarkan seberapa baru lowongan tersebut.
                    - **Kesesuaian Industri dan Peran (10%)**: Latar belakang kandidat vs. jenis industri/peran pekerjaan.
                    - **Kesesuaian Lokasi atau Remote (5%)**: Apakah kandidat sesuai dengan syarat lokasi atau remote.
                    - **Kesesuaian Sertifikasi (5%)**: Apakah kandidat memiliki sertifikasi yang dibutuhkan atau relevan.

                    ### Multiplikator Berdasarkan Usia Lowongan
                    | Usia Lowongan | Hari | Multiplikator | Label |
                    |---------------|------|----------------|--------|
                    | 0–3 hari      | ≤ 3  | 1.5x           | 🔥 SEGERA — Lamar sekarang  
                    | 4–7 hari      | ≤ 7  | 1.3x           | ⚡ TINGGI — Lamar minggu ini  
                    | 8–14 hari     | ≤ 14 | 1.1x           | 📈 BIASA — Waktu standar  
                    | 15–21 hari    | ≤ 21 | 1.0x           | ⏰ SEGERA BERAKHIR  
                    | 22–30 hari    | ≤ 30 | 0.9x           | ⚠️ MENUJU KADALUARSA  
                    | 31+ hari      | > 30 | 0.7x           | ❌ SUDAH TUA  

                    ## 🏆 SKOR KEC0COKAN
                    - **95–100**: Sangat Cocok 🎯 — Kandidat ideal, segera lamar.
                    - **85–94**: Cocok Banget ⭐ — Kandidat sangat kuat.
                    - **75–84**: Cocok ✅ — Ada celah kecil, tapi sangat potensial.
                    - **65–74**: Cukup ⚠️ — Bisa dipertimbangkan dengan persiapan.
                    - **< 65**: Kurang ❌ — Tidak disarankan kecuali ada peningkatan.

                    ## 📤 FORMAT OUTPUT

                    ### Peringkat #X: [Judul Pekerjaan] di [Perusahaan]
                    **Skor Akhir: XX/100** [Label Penilaian]  
                    **Skor Dasar: XX | Multiplikator Waktu: X.Xx | Skor Disesuaikan: XX**  
                    **Diposting: X hari yang lalu** [Label Urgensi]

                    **🔍 Kekuatan (Cocok):**
                    - [Kecocokan #1]
                    - [Kecocokan #2]
                    - [Kecocokan #3]

                    **❌ Kelemahan (Gaps):**
                    - [Skill/pengalaman yang kurang] (Kritis/Sedang/Ringan)

                    **📈 Rekomendasi:**
                    - Apakah kandidat sebaiknya melamar? Kapan waktu yang tepat?
                    - Persiapan yang perlu dilakukan sebelum melamar (skill, sertifikasi, dll)
                    - Tingkat kesiapan untuk wawancara

                    ---

                    ## ⚙️ ATURAN ANALISIS
                    1. Hanya gunakan informasi yang tersedia — jangan membuat asumsi.
                    2. Prioritaskan **keterampilan dan pengalaman** sebagai faktor utama.
                    3. Sesuaikan skor berdasarkan **multiplikator usia lowongan**.
                    4. Untuk setiap lowongan, hitung **skor dasar**, terapkan **multiplikator waktu**, lalu hasilkan **skor akhir**.
                    5. Urutkan dan tampilkan **10 lowongan dengan skor tertinggi**.
                    6. Sertakan alasan rekomendasi dalam format poin-poin.

                    ---

                    ## 🧠 PEDOMAN NORMALISASI KETERAMPILAN

                    Saat membandingkan keterampilan kandidat dengan persyaratan pekerjaan:

                    - Normalisasi keterampilan yang merujuk pada teknologi yang sama meskipun ditulis berbeda.
                    - Perlakukan sinonim, singkatan, versi, atau variasi nama sebagai satu keterampilan yang sama.
                    - Contoh: `"React.js"`, `"ReactJS"` → **React**, `"GCP"`, `"Google Cloud"` → **Google Cloud Platform**.

                    💡 Gunakan pemahaman teknis dan akal sehat untuk **mengelompokkan keterampilan yang sebenarnya setara** demi pencocokan yang adil dan akurat.

                    ⚠️ Jangan penalti kandidat hanya karena perbedaan penulisan keterampilan. Fokus pada **kesetaraan semantik**, bukan pencocokan teks secara literal.

                    Selalu dasarkan penilaian dan analisis gap berdasarkan keterampilan yang telah dinormalisasi.

                    ---

                    ## 📂 LOWONGAN UNTUK DIEVALUASI
                    {formatted_jobs}

                    Silakan kembalikan hasil rekomendasi pekerjaan yang telah diperingkat berdasarkan kerangka di atas.
                    """)

            pm_batch.add_message("user", f"""
                    PROFIL KANDIDAT:
                    {parsed_cv}

                    KETERAMPILAN KANDIDAT:
                    {skills}

                    PENGALAMAN KERJA:
                    {experience}

                    TUGAS:
                    Evaluasilah profil kandidat berdasarkan daftar lowongan pekerjaan yang telah disediakan, menggunakan kerangka penilaian di atas. Fokus pada evaluasi yang objektif. Jangan membuat asumsi terhadap data yang tidak tersedia.

                    OUTPUT YANG DIHARAPKAN:
                    🎯 LAPORAN REKOMENDASI PEKERJAAN

                    ## Ringkasan Eksekutif
                    - Ringkasan singkat (2–3 kalimat) mengenai kecocokan dan kekuatan kandidat di pasar kerja saat ini.

                    ## Peringkat Rekomendasi

                    ### Peringkat #1: [Posisi Pekerjaan] di [Perusahaan]
                    **Skor Akhir: XX/100** [Label Penilaian]  
                    **Skor Dasar: XX | Multiplikator Waktu: X.Xx | Skor Disesuaikan: XX**  
                    **Diposting: X hari yang lalu** [Label Urgensi]

                    **✔ Kekuatan Utama:**
                    - [Skill/pengalaman #1]
                    - [Skill/pengalaman #2]
                    - [Skill/pengalaman #3]

                    **⚠️ Kelemahan (Gap):**
                    - [Persyaratan yang belum terpenuhi] (Kritis/Sedang/Ringan)

                    **📌 Rekomendasi:**
                    - Apakah kandidat cocok untuk melamar pekerjaan ini? Kapan waktu terbaik untuk melamar?
                    - Apa saja yang harus dipersiapkan (misalnya skill tambahan, sertifikasi, dll)
                    - Tingkat kesiapan untuk mengikuti wawancara

                    **📍 Rencana Tindakan:**
                    - [Langkah awal yang bisa dilakukan segera]
                    - [Persiapan jangka pendek]

                    **⏳ Perkiraan Waktu Siap:** [Siap Sekarang / 2–4 minggu / 1–3 bulan]

                    ---

                    [Ulangi bagian ini hingga 5–7 rekomendasi pekerjaan terbaik]

                    ## 📊 Ringkasan Analisis

                    **Jalur Karier yang Paling Cocok:**
                    - [Jalur 1]: [Penjelasan singkat]
                    - [Jalur 2]: [Penjelasan singkat]

                    **Keterampilan yang Perlu Dikembangkan (Prioritas Utama):**
                    - [Skill #1]
                    - [Skill #2]

                    **Posisi Kandidat di Pasar Kerja:**
                    - [Kalimat ringkas mengenai daya saing kandidat berdasarkan hasil pencocokan]

                    PETUNJUK:
                    - Gunakan hanya data dari profil kandidat dan lowongan pekerjaan yang tersedia.
                    - Urutkan lowongan berdasarkan skor akhir setelah dikalikan dengan multiplikator waktu.
                    - Jangan membuat asumsi. Dasarkan semua kesimpulan hanya pada data yang diberikan.

                    ## 🧠 PEDOMAN NORMALISASI KETERAMPILAN

                    Saat membandingkan keterampilan kandidat dengan persyaratan pekerjaan:

                    - Normalisasikan keterampilan yang merujuk pada teknologi yang sama, meskipun tertulis berbeda.
                    - Perlakukan nama alternatif, singkatan, ekstensi, atau variasi penulisan sebagai keterampilan yang sama.
                    - Contoh: "React.js", "ReactJS" → **React**; "Git", "Git version control" → **Git**; "Google Cloud", "GCP" → **Google Cloud Platform**

                    💡 Gunakan penalaran teknis dan pemahaman umum untuk **mengelompokkan keterampilan yang secara semantik setara** agar pencocokan adil dan akurat.

                    ⚠️ Jangan memberikan penalti hanya karena perbedaan penulisan. Fokus pada **kesamaan makna**, bukan pencocokan teks literal.

                    Dasarkan seluruh penilaian dan analisis gap pada bentuk keterampilan yang telah dinormalisasi.
                    """)



            try:
                result_batch = pm_batch.generate_structure(MatchingJob)
                matched_jobs = result_batch.get("jobs", [])
                for job in matched_jobs:
                    logger.info(f"Matched Job: {job['title']} at {job['company']} with score {job['match_score']}")
                logger.info(f"✅ Batch {batch_index}: {len(matched_jobs)} matched jobs")
                all_matched_jobs.extend(matched_jobs)
            except Exception as e:
                logger.warning(f"❌ Gagal memproses batch {batch_index}: {e}")
                continue

        logger.info(f"Total matched jobs from all batches: {len(all_matched_jobs)}")

        for idx, job in enumerate(all_matched_jobs, 1):
            job_instance = Job.objects.filter(id=job['job_id']).first()
            if job_instance:
                JobRecommendation.objects.filter(user=user, job=job_instance).delete()
                recommendation, created_rec = JobRecommendation.objects.update_or_create(
                    user=user,
                    job=job_instance,
                    defaults={
                        "score": job["match_score"],
                        "recommended_at": timezone.now()
                    },
                    matched_skills=job["matched_skills"],
                    reason=job["reason"]
                )
                if created_rec:
                    logger.info(f"✅ JobRecommendation #{idx} berhasil disimpan untuk user {user.username}.")
                else:
                    logger.info(f"⚠️ JobRecommendation #{idx} sudah ada untuk user {user.username}, dilewati.")
            else:
                logger.info(f"❌ Job {job['title']} di {job['company']} tidak ditemukan di database.")

        send_notification({
            "type": "success",
            "title": "🎉 Pencocokan Selesai",
            "message": f"Kami menemukan {len(all_matched_jobs)} pekerjaan yang cocok dengan profil Anda. Lihat rekomendasinya sekarang!"
        })


    except Exception as e:
        logger.error(f"❌ Gagal menghapus atau menyimpan job recommendation: {e}")
        send_notification({
            "type": "error",
            "title": "🔥 Proses Pencocokan Gagal",
            "message": "Maaf, terjadi kesalahan saat menyimpan hasil rekomendasi Anda. Silakan coba beberapa saat lagi."
        })
        raise e
