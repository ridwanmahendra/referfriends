import os
import streamlit as st
import openai
import requests
from dotenv import load_dotenv
import time
from io import StringIO

# Load API keys dari .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")

# Fungsi untuk mencari jurnal menggunakan Semantic Scholar API
def search_papers(query):
    headers = {"x-api-key": semantic_scholar_api_key}
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={query}&fields=title,authors,url,abstract,venue,year"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if "data" in data:
            return data["data"]
        else:
            st.error("Tidak ada data ditemukan untuk kueri ini.")
            return []
    else:
        st.error("Gagal mendapatkan data dari Semantic Scholar.")
        st.write(response.text)  # Untuk debugging
        return []

def create_journal_file(papers):
    buffer = StringIO()
    for idx, paper in enumerate(papers, 1):
        buffer.write(f"({idx}) {paper['title']}\n")
        authors = ', '.join([author['name'] for author in paper['authors']])
        buffer.write(f"Authors: {authors}\n")
        buffer.write(f"Year: {paper['year']} - Venue: {paper['venue']}\n")
        buffer.write(f"URL: {paper['url']}\n")
        if paper.get('abstract'):
            buffer.write(f"Abstract: {paper['abstract']}\n")
        buffer.write("\n---\n\n")
    
    buffer.seek(0)
    return buffer.getvalue()

# Fungsi untuk menganalisis hubungan teks dengan jurnal
def analyze_relationship(input_text, papers):
    abstracts = "\n".join([paper['abstract'] for paper in papers if paper.get('abstract')])
    prompt = f"Analyze the relationship between the following input text and the abstracts of several academic papers.\n\nInput Text:\n{input_text}\n\nAbstracts:\n{abstracts}\n\nProvide a summary of the relationship:"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an academic assistant that helps analyze relationships between texts and research papers."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300,
        temperature=0.5,
    )

    analysis = response.choices[0].message['content'].strip()
    return analysis

# Streamlit UI
st.set_page_config(page_title="Research Paper Citation Generator", layout="wide")
st.title("Research Paper Citation Generator")


# Input dari user
input_text = st.text_area("Masukkan teks atau pertanyaan:")

# Tombol untuk mencari jurnal
if st.button("Cari Jurnal"):
    if input_text:
        papers = search_papers(input_text)
        
        if papers:
            # Membuat dua kolom: satu untuk Papers, satu lagi untuk Insights
            col1, col2 = st.columns(2)
            
            # Menampilkan Papers di kolom kiri
            with col1:
                st.subheader(f"Papers ({len(papers)})")
                for idx, paper in enumerate(papers, 1):
                    st.markdown(f"### ({idx}) {paper['title']}")
                    authors = ', '.join([author['name'] for author in paper['authors']])
                    st.markdown(f"*{authors}*\n")
                    st.markdown(f"*{paper['year']} - {paper['venue']}*")
                    st.markdown(f"**[Baca selengkapnya]({paper['url']})**")
                    if paper.get('abstract'):
                        st.markdown(f"\n{paper['abstract']}\n")
                    st.markdown("---")
                    time.sleep(1)  # Jeda untuk memenuhi rate limit
                    
                # Menambahkan tombol download untuk file teks
                journal_file = create_journal_file(papers)
                st.download_button(
                label="Download Jurnal",
                data=journal_file,
                file_name="journals.txt",
                mime="text/plain"
            )

            # Menampilkan Insights di kolom kanan
            with col2:
                analysis = analyze_relationship(input_text, papers)
                st.subheader("Insights")
                st.write(analysis)
    else:
        st.warning("Silakan masukkan teks atau pertanyaan.")
