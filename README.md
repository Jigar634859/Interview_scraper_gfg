## Project Summary

This project provides a fully automated, synchronized pipeline to generate professional SDE interview preparation materials for any company, leveraging real-world interview experiences from GeeksforGeeks. The workflow covers:

- **Web scraping** of company-specific interview experiences.
- **Role inference** (SDE-1, SDE-2, SDE-3) based on experience years.
- **Automated summarization** of each interview using advanced AI models (Groq's gemma2-9b-it and deepseek-r1-distill-llama-70b).
- **Aggregation** of summaries into a comprehensive, well-structured markdown report.
- **Extraction of coding question links** for quick reference.
- **PDF generation** with professional styling, clickable links, and a topic distribution pie chart for visual analytics.

Final outputs include:
- Individual interview summaries (CSV)
- Aggregated summary (CSV)
- Coding question links table (CSV)
- A polished PDF report for interview preparation

This solution is ideal for anyone seeking a structured, data-driven approach to SDE interview prep, especially for SDE-1 roles.

---

## How to Run

1. **Install Dependencies**

   ```bash
   pip install pandas requests beautifulsoup4 groq markdown weasyprint matplotlib python-dotenv
   ```

2. **Set Up API Key**

   - Create a `.env` file in your project directory with:
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```

3. **Run the Pipeline**

   - Execute the main script:
     ```bash
     python your_script_name.py
     ```

   - When prompted, enter the company name (e.g., `Amazon`) and the desired role (e.g., `SDE-1`).

4. **Outputs**

   - Check your project folder for:
     - `__individual_summaries.csv`
     - `__final_summary.csv`
     - `_coding_questions.csv`
     - `__summary.pdf`

---

**Note:**  
- The script is fully automated and requires only minimal user input (company and role).
- Ensure you have a valid Groq API key for AI summarization.
- PDF and CSV outputs are ready for direct use in interview preparation or sharing.


