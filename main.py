import streamlit as st
import PyPDF2
import io
import os
from dotenv import load_dotenv
import docx
import markdown
import pdfkit

load_dotenv(dotenv_path=".env")

st.set_page_config(page_title="AI Resume Critiquer", layout="centered")
st.title("AI Resume Critiquer")
st.markdown("Upload your resume and get AI-powered feedback tailored to your needs!")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(docx_file):
    doc = docx.Document(docx_file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

def create_pdf_from_markdown(md_text):
    html = markdown.markdown(md_text, extensions=['extra', 'smarty'])
    html_doc = f"""
    <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: "DejaVu Sans", Arial, sans-serif; padding: 2em; font-size: 1.1em; color: #1a202c; background: #fff; }}
                h1, h2, h3, h4 {{ color: #2d3748; margin-top: 1.2em; }}
                ul, ol {{ margin-left: 1.5em; }}
                strong {{ font-weight: bold; color: #2d3748; }}
                em {{ font-style: italic; color: #6b7280; }}
                code {{ background: #f3f4f6; border-radius: 4px; padding: 2px 4px; font-size: 95%; color: #374151; }}
                hr {{ border: none; border-top: 1px solid #e2e8f0; margin: 1.5em 0; }}
                blockquote {{ border-left: 4px solid #a0aec0; margin: 1em 0; padding-left: 1em; color: #4a5568; background: #f7fafc; }}
            </style>
        </head>
        <body>{html}</body>
    </html>
    """
    # Якщо wkhtmltopdf не у PATH, явно вкажи шлях:
    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    pdf_bytes = pdfkit.from_string(html_doc, False, configuration=config)
    return pdf_bytes

# STREAMLIT UI

uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX or TXT)", type=["pdf", "txt", "docx"])
job_role = st.text_input("Enter the job role you're targeting (optional)")
analyze = st.button("Analyze Resume")

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

        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = [
                {"role": "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        analysis_text = response.choices[0].message.content
        st.session_state['analysis_text'] = analysis_text

    except Exception as e:
        st.error(f"An error has happened")
        print(e)
        print(os.getenv("OPENAI_API_KEY"))

# --- Відображення результату та кнопок
if 'analysis_text' in st.session_state:
    st.markdown("### Analysis Results")
    st.markdown(st.session_state['analysis_text'])
    pdf_bytes = create_pdf_from_markdown(st.session_state['analysis_text'])
    st.download_button(
        label="Download analysis as PDF",
        data=pdf_bytes,
        file_name="analysis.pdf",
        mime="application/pdf"
    )
    if st.button("🗑️ Очистити результат"):
        del st.session_state['analysis_text']
