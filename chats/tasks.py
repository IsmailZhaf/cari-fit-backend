from huey.contrib.djhuey import task
from core.ai.pm import PromptManager
from .methods import send_chat_message
from chats.models import Conversation
from core.ai.chromadb import chroma_client, embedding_function
from cv.models import CV
from jobs.models import Job 
from pydantic import BaseModel, Field

class analyze_message(BaseModel):
    is_true: bool = Field(description="Bernilai true jika pertanyaan relevan, jika tidak maka bernilai false")


def analyze_question(message):
    pm = PromptManager()
    pm.add_message("system", """Tugas kamu adalah menganalisis apakah pertanyaan yang diajukan
        relevan mengenai analisis cv, lowongan pekerjaan atau kesesuaian antara cv user dengan lowongan.
        sehingga user tidak bisa mengajukan pertanyaan yang tidak relevan.

        Jika pertanyaan tidak sesuai maka jawab false, jika sesuai maka jawab true
     """)
    pm.add_message("user", message)
    result = pm.generate_structure(analyze_message)
    print("is true: ",result['is_true'])
    return result['is_true']

@task()
def process_chat(message, document_id, cv_id):
    is_relevant = analyze_question(message)

    if not is_relevant:
        response = (    
            "Maaf, saya hanya bisa membantu pertanyaan seputar CV dan lowongan pekerjaan. "
            "Silakan ajukan pertanyaan yang relevan, seperti kecocokan CV dengan pekerjaan tertentu."
        )
        Conversation.objects.create(message=message, role="user")
        Conversation.objects.create(message=response, role="assistant")
        send_chat_message(response)
        return 

    # Simpan pesan user ke database
    Conversation.objects.create(message=message, role="user")


    # Ambil parsed_text dari CV user
    try:
        cv = CV.objects.get(id=cv_id)
        cv_text = cv.parsed_text
    except CV.DoesNotExist:
        cv_text = "CV tidak ditemukan."

    # Ambil informasi lowongan berdasarkan document_id
    try:
        job = Job.objects.get(id=document_id)
        job_text = (
    f"Judul Pekerjaan: {job.job_title or '-'}\n"
    f"Nama Perusahaan: {job.company_name or '-'}\n"
    f"Industri Perusahaan: {job.company_industry or '-'}\n"
    f"Deskripsi Perusahaan: {job.company_desc or '-'}\n"
    f"Ukuran Perusahaan: {job.company_employee_size or '-'}\n"
    f"Industri Pekerjaan: {job.industry or '-'}\n"
    f"Lokasi: {job.location or '-'}\n"
    f"Tipe Pekerjaan: {job.job_type or '-'}\n"
    f"Level Pengalaman: {job.experience_level or '-'}\n"
    f"Tingkat Pendidikan: {job.education_level or '-'}\n"
    f"Gaji: {job.salary or '-'}\n"
    f"Tanggal Diposting: {job.date_posted or '-'}\n"
    f"Keahlian yang Dibutuhkan: {job.skills_required or '-'}\n"
    f"Deskripsi Pekerjaan:\n{job.job_description or '-'}\n"
    f"Link Lowongan: {job.url}\n"
)
    except Job.DoesNotExist:
        job_text = "Informasi lowongan tidak ditemukan."

    # Ambil semua chat sebelumnya
    chats = Conversation.objects.all()
    messages = [
        {
            "role": "system",
            "content": (f"""
            Kamu adalah asisten virtual yang hanya boleh menjawab pertanyaan seputar CV dan lowongan kerja.
            Kamu adalah asisten cerdas dan informatif yang membantu pengguna memahami CV mereka, menganalisis lowongan pekerjaan, serta memberikan perbandingan yang jelas antara keduanya.
            Berikan jawaban yang ringkas, akurat, dan mudah dipahami.
            Jika pengguna menanyakan tentang kecocokan, bantu jelaskan bagian mana dari CV yang sesuai dengan persyaratan pekerjaan.
            User CV:{cv_text}
            Job Posting:{job_text}

            Dilarang menjawab pertanyaan yang tidak terkait dengan CV atau lowongan kerja, termasuk topik umum seperti politik, hiburan, atau pribadi.

            Jika pertanyaan tidak relevan, jawab dengan: 
            "Maaf, saya hanya bisa membantu pertanyaan seputar CV dan lowongan pekerjaan."

            Ingat: Jangan pernah melanggar batasan ini.
            """
            ),
        }
    ]

    for chat in chats:
        messages.append({"role": chat.role, "content": chat.message})

    # Generate response
    prompt = PromptManager()
    prompt.set_messages(messages)
    response = prompt.generate()

    Conversation.objects.create(message=response, role="assistant")
    send_chat_message(response)

    print("=== Response ===")
    print(response)
