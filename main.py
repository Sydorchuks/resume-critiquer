import streamlit as st
import PyPDF2
import io
import os 
from openai import OpenAI
from dotenv import load_dotenv
import docx
from fpdf import FPDF
import markdown
from weasyprint import HTML

load_dotenv(dotenv_path=".env")

st.set_page_config(page_title="AI Resume Critiquer", page_icon = "", layout="centered")

st.title("AI Resume Critiquer")
st.markdown("Upload your resume and get AI-powered feedback tailored to your needs!")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type=["pdf", "txt"])
job_role = st.text_input("Enter the job role you're targeting (optional)")

analyze = st.button("Analyze Resume")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)


def create_pdf(text, filename="analysis.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    # Зберігаємо в bytes замість файлу
    pdf_output = pdf.output(dest='S').encode('latin1')
    return pdf_output



def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(io.BytesIO(uploaded_file.read()))

    return uploaded_file.read().decode("utf-8")

if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)

        if not file_content.strip():
            st.error("File does not have any content...")
            st.stop()
        
        prompt = f"""Please analyze this resume and provide constructive feedback without sugarcoating.
        Focus on the following aspects:
        1. Content Clarity and impact
        2. Skills presentation
        3. Experience descriptions
        4. Specific improvements for {job_role if job_role else "general job applications"}
        
        Resume content: {file_content}
        
        Please provide your analysis in a clear, structured format with specific recommendations."""

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role": "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        st.markdown("### Analysis Results")
        st.markdown(response.choices[0].message.content)

        pdf_bytes = create_pdf(response.choices[0].message.content)
        st.download_button(
            label="Download analysis as PDF",
            data=pdf_bytes,
            file_name="analysis.pdf",
            mime="application/pdf"
        )

    except Exception as e: 
        st.error(f"An error has happened")
        print(e)
        print(os.getenv("OPENAI_API_KEY"))
