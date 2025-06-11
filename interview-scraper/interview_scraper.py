import os
import time
import re
import pandas as pd
from io import BytesIO
import base64
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
from groq import Groq
import matplotlib.pyplot as plt
from weasyprint import HTML
import markdown

client = Groq(api_key=os.getenv("GROQ_API_KEY", "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"))
BASE_URL = "https://www.geeksforgeeks.org/interview-experiences/experienced-interview-experiences-company-wise/"

def infer_role_and_years(title):
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:yr|year)', title, re.IGNORECASE)
    yrs = float(m.group(1)) if m else 0.0
    if yrs <= 2: return yrs, 'SDE-1'
    elif yrs <= 5: return yrs, 'SDE-2'
    return yrs, 'SDE-3'

def scrape_company_experiences(company):
    soup = BeautifulSoup(requests.get(BASE_URL).text, "lxml")
    label_node = soup.find(string=re.compile(rf'^\s*{re.escape(company)}\s*:$'))
    if not label_node:
        print(f"❌ Could not locate section for '{company}'.")
        return []
    entries = []
    for elem in label_node.next_elements:
        if isinstance(elem, NavigableString) and re.match(r'^\s*[A-Za-z0-9 &]+\s*:$', elem.strip()) and elem.strip() != f"{company}:":
            break
        if isinstance(elem, Tag) and elem.name == "a" and elem.get("href"):
            title = elem.get_text(strip=True)
            link = elem["href"]
            yrs, role = infer_role_and_years(title)
            entries.append({"Company": company, "Title": title, "Link": link, "Years": yrs, "Role": role})
    return entries

def fetch_full_text(link):
    soup = BeautifulSoup(requests.get(link, headers={'User-Agent': 'Mozilla/5.0'}).text, 'html.parser')
    text_div = soup.find('div', class_='text') or soup.find('div', class_='entry-content') or soup.find('article') or soup.body
    return str(text_div) if text_div else ''

def summarize_single_experience(html_content):
    if pd.isnull(html_content): return ""
    soup = BeautifulSoup(html_content, 'html.parser')
    clean_text = soup.get_text(separator=' ', strip=True)

    prompt = f"""
You are given a software-engineering interview write-up in HTML. Extract and summarize it in 3–5 bullet points.

Cover:
- Technical questions asked (by topic: Array, Tree, String, DP, Graph)
- System design components
- Behavioral questions
- Interview structure/rounds

Preserve markdown links from `<a>` tags like `[Question](URL)`.

---
**Text:** {clean_text[:3000]}
---
**HTML:** {html_content[:3000]}
"""

    try:
        completion = client.chat.completions.create(
            model="gemma2-9b-it",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_completion_tokens=400
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error summarizing: {e}")
        return ""

def generate_final_summary(merged_summary,role):
    prompt = f"""
You are an expert technical interviewer.

Given merged {role.upper()} summaries, generate a detailed report for a prep PDF.

Include:
- Key topics (Array, Tree, String, DP, Graph, System Design)
- Behavioral questions & sample answers
- Coding questions with links
- System design topics
- Interview structure
- Common advice/tips

Format professionally in markdown.

---
{merged_summary[:6000]}
---
"""
    try:
        completion = client.chat.completions.create(
            model="deepseek-r1-distill-llama-70b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_completion_tokens=2048
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error finalizing summary: {e}")
        return ""

def export_cleaned_pdf(company, role, summary_md, output_path):
    # Remove <think>...</think>
    summary_md_cleaned = re.sub(r'<think>.*?</think>', '', summary_md, flags=re.DOTALL | re.IGNORECASE)

    # Analyze topic distribution
    topics = ['Array', 'Tree', 'String', 'DP', 'Graph', 'System Design', 'Behavioral Questions']
    topic_counts = {
        topic: len(re.findall(rf'\b{topic}\b', summary_md_cleaned, flags=re.IGNORECASE))
        for topic in topics
    }
    topic_counts = {k: v for k, v in topic_counts.items() if v > 0}

    # Pie chart
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(topic_counts.values(), labels=topic_counts.keys(), autopct='%1.1f%%', startangle=140)
    ax.set_title("Topic Distribution in Interview Summary")
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    img_html = f'<img src="data:image/png;base64,{img_base64}" alt="Topic Distribution Chart" style="max-width:100%; height:auto;">'

    # Convert markdown to HTML
    html_summary = markdown.markdown(summary_md_cleaned, extensions=['extra', 'tables', 'sane_lists'])

    # Final HTML with styles
    styled_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 1in; }}
            body {{
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #333;
                line-height: 1.6;
            }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            a {{ color: #1e88e5; text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>{company} - {role} Interview Preparation Summary</h1>
        <h2>📊 Topic Distribution</h2>
        {img_html}
        <hr>
        {html_summary}
    </body>
    </html>
    """
    HTML(string=styled_html, base_url='.').write_pdf(output_path)
    print(f"✅ PDF created: {output_path}")

def orchestrate_full_pipeline():
    company = input("Enter Company name: ").strip()
    role = input("Enter Role (e.g. SDE-1): ").strip()

    print("🔍 Scraping...")
    entries = scrape_company_experiences(company)
    if not entries:
        return

    df = pd.DataFrame(entries)
    df = df[df['Role'].str.upper() == role.upper()]
    if df.empty:
        print(f"❌ No entries found for {role}")
        return

    print("📥 Fetching interview content...")
    df['Interview_Experience'] = [fetch_full_text(link) for link in df['Link']]

    print("🧠 Summarizing interviews...")
    df['Interview_Summary'] = [summarize_single_experience(html) for html in df['Interview_Experience']]
    df.to_csv(f"{company.lower()}_{role.lower()}_individual_summaries.csv", index=False)

    print("📄 Generating final markdown summary...")
    merged_summary = '\n'.join(df['Interview_Summary'].astype(str))
    final_summary = generate_final_summary(merged_summary,role)

    # Save to CSV
    summary_csv_path = f"{company.lower()}_{role.lower()}_final_summary.csv"
    pd.DataFrame({'Summary': [final_summary]}).to_csv(summary_csv_path, index=False)
    print(f"📝 Summary saved to {summary_csv_path}")

    # Extract coding question links
    print("🔗 Extracting coding links...")
    matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+)\)', final_summary)
    pd.DataFrame(matches, columns=['Question', 'Link']).to_csv(f"{company.lower()}_coding_questions.csv", index=False)

    # PDF with styled HTML and chart
    print("📄 Building PDF...")
    export_cleaned_pdf(company, role, final_summary, f"{company.lower()}_{role.lower()}_summary.pdf")

if __name__ == "__main__":
    orchestrate_full_pipeline()
