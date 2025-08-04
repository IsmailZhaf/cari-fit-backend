from cv.models import CV  # di awal, biar tidak di dalam fungsi
from django.contrib.auth import get_user_model
from notifications.methods import send_notification
from core.ai.mistral import mistral_client
from core.ai.pm import PromptManager
from cv.utils import clean_cv_text
from huey.contrib.djhuey import task
from dotenv import load_dotenv
from matching.task import job_matching
from pydantic import BaseModel, Field
from typing import List, Literal
import os

load_dotenv()

CategoryLiteral = Literal["Teknologi", "Bisnis dan Manajemen", "Kreatif", "Industri dan Manufaktur", "None"]

class AnalyzeCV(BaseModel):
    category: CategoryLiteral = Field(
        ..., 
        description="Kategori Pekerjaan, harus salah satu dari: Teknologi, Bisnis dan Manajemen, Kreatif, Industri dan Manufaktur"
    )
    skills: str = Field(description="skill yang ada pada cv")
    is_CV: bool = Field(description="tentukan apakah dokumen tersebut adalah CV atau bukan, CV memiliki strukur: informasi pribadi, ringkasan profil, riwayat pendidikan, pengalaman kerja, keahlian, dan sertifikasi/pelatihan.")
    experience: str = Field(description="pengalaman kerja atau proyek yang ada pada cv, bisa juga pengalaman organisasi")


@task()
def process_cv(cv_id):
    try:
        cv = CV.objects.get(id=cv_id)
    except CV.DoesNotExist:
        print(f"CV with ID {cv_id} not found.")
        return False

    try:
        cv.status = "processing"
        cv.save()

        send_notification({
            "type": "info",
            "title": "🔎 Mulai Memproses",
            "message": "Kami sedang menganalisis CV Anda dan mencari lowongan pekerjaan yang paling cocok..."
        })

        file_path = cv.file_url
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Upload dan OCR
        with open(file_path, "rb") as file_content:
            uploaded_file = mistral_client.files.upload(
                file={
                    "file_name": os.path.basename(file_path),
                    "content": file_content,
                },
                purpose="ocr"
            )
        signed_url = mistral_client.files.get_signed_url(file_id=uploaded_file.id)
        ocr_response = mistral_client.ocr.process(
            model="mistral-ocr-2505",
            document={"type": "document_url", "document_url": signed_url.url}
        )

        parsed_text = "\n\n".join(page.markdown for page in ocr_response.pages)
        cleaned_text = clean_cv_text(parsed_text)

        # Analisis AI
        pm = PromptManager()
        pm.add_message("system", f"""
            Kamu adalah asisten rekrutmen profesional.

            Tugasmu adalah menentukan apakah **dokumen yang diberikan benar-benar merupakan CV (Curriculum Vitae)** atau **bukan**.

            ### Definisi CV yang Sah:
            CV wajib berisi sebagian besar dari elemen-elemen berikut ini:
            - Informasi pribadi
            - Ringkasan profil atau tujuan karier
            - Riwayat pendidikan
            - Pengalaman kerja
            - Daftar keterampilan
            - Sertifikasi/pelatihan (opsional)

            Jika hanya berupa identitas seperti KTP, SIM, atau cover letter → bukan CV.

            Dokumen:
            {cleaned_text}
        """)
        pm.add_message("user", "Tolong kembalikan struktur data CV yang dianalisis.")
        result = pm.generate_structure(AnalyzeCV)

        is_cv = result["is_CV"]
        category = result["category"] or "None"  # Jaga-jaga agar tidak None
        skills = result["skills"]
        experience = result['experience']

        # Tangani dokumen bukan CV
        if not is_cv:
            send_notification({
                "type": "error",
                "title": "❌ Dokumen Tidak Valid",
                "message": "Dokumen yang diunggah bukan CV atau tidak dapat dianalisis. Silakan unggah ulang dokumen Anda."
            })
            return False

        # Jika CV valid
        cv.parsed_text = cleaned_text
        cv.category = category
        cv.status = "completed"
        cv.save()

        user = get_user_model().objects.get(id=cv.user_id)
        job_matching(user, cv.id, skills, experience)

        print("CV processed successfully")
        return True

    except Exception as e:
        print(f"Error processing CV {cv_id}: {str(e)}")

        if cv:
            try:
                if not cv.category or cv.category is None:
                    cv.category = "None"  # <- pastikan kategori aman
                if not cv.parsed_text:
                    cv.parsed_text = ""  # <- biar aman juga
                cv.status = "failed"
                cv.save()

                send_notification({
                    "type": "error",
                    "title": "❌ Gagal Memproses",
                    "message": "Gagal mengunggah atau memproses CV Anda. Silakan coba kembali."
                })
            except Exception as save_error:
                print(f"❗ Gagal menyimpan status gagal: {str(save_error)}")

        raise e
