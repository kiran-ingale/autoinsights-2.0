# AutoInsights Prototype Demo

## Start the app

```powershell
cd C:\Users\user\Desktop\codex
.\myenv\Scripts\Activate.ps1
$env:PYTHONPATH="."
streamlit run frontend/streamlit_app.py
```

Open the local URL shown by Streamlit, normally `http://localhost:8501`.

## Demo flow

1. Enter `Analyze retail sales trends` as the question.
2. Select **Use the included retail sales sample data instead**.
3. Select **Start analysis**.
4. Review the raw-data dashboard, data-quality notices, findings, visualizations, and proposed cleaning plan.
5. Download the raw-data HTML report if desired.
6. Select **Execute cleaning and refresh analysis**.
7. Review the cleaned-data dashboard, applied transformation log, and final HTML report.

## Chat demo

After adding `MISTRAL_API_KEY` to `.env` and restarting Streamlit, try these requests in the chatbox:

- `What are the key findings?`
- `Explain the correlation chart.`
- `What cleaning will be applied?`
- `Execute the cleaning.`
- `Where is the report?`

The chat router can answer analysis questions and invoke only supported local workflow actions. It cannot execute arbitrary system commands or access external services beyond the configured Mistral or Groq API.

## Expected artifacts

Each run writes files to `artifacts/<run_id>/`:

```text
input.csv
assessment_report.html
cleaned.csv
transformations.json
metadata.json
report.html
```

## Final verification

```powershell
pytest tests -q
```

The current expected result is `16 passed`.
