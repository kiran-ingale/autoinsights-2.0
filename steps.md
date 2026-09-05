1. Set up the project folders, virtual environment, .gitignore, sample CSV, and Streamlit placeholder.
2. Define the shared contracts:
   - AnalysisRequest
   - AnalysisState
   - Artifact folder format
   - run_analysis(request, uploaded_file) function signature
3. Build the LangGraph skeleton with placeholder nodes and routing.
4. Implement core data agents:
   - Intake and CSV validation
   - Sample-data acquisition
   - Data profiling
   - Data cleaning with transformation logs
5. Implement analytical agents:
   - EDA
   - Feature preparation
   - Statistics/correlation
   - Insight generation
   - Visualization metadata
6. Connect the Streamlit input form to the graph:
   - Upload CSV
   - Add question/domain/constraints
   - Run analysis
   - Show progress and errors
7. Build the Streamlit dashboard:
   - KPI cards
   - Plotly charts
   - Data-quality warnings
   - Cleaned-data explorer
   - Findings and recommendations
8. Add artifact handling:
   - Save input and cleaned CSVs
   - Save transformation logs and charts
   - Create an HTML report
   - Add download buttons
9. Test with clean, time-series, and messy datasets.
10. Integrate branches, fix contract mismatches, update README, and prepare the demo.


