# CrimeSight Advanced

CrimeSight is a responsive, light-theme dashboard for exploring aggregate historical crime records. It includes interactive charts, two category classifiers (Random Forest and Extra Trees), an optional crime-rate regression estimate, downloadable CSV records, and JSON API endpoints.

> **Responsible use:** This is an academic analytics prototype. The classifier estimates a category label found in the supplied dataset; it does not predict whether a crime will happen. A model score is not the probability of a crime. Do not use the output for policing, surveillance, individual risk scoring, or other high-impact decisions.

## Project structure

```text
CrimeSight_Advanced/
├── app.py
├── requirements.txt
├── crime1_data.xlsx
├── crime_data.csv
├── templates/
│   ├── index.html
│   └── result.html
├── tests/
│   └── test_app.py
├── run_windows.bat
├── .gitignore
└── README.md
```

## Requirements

- Python 3.10–3.12 recommended
- Internet connection during first install to download Python packages (the app itself uses the local dataset)
- VS Code or another editor is optional

Python 3.13 may work with compatible package versions, but Python 3.12 is recommended for a predictable student setup.

## Run on Windows

1. Extract the ZIP file.
2. Open the extracted `CrimeSight_Advanced` folder in VS Code.
3. Open a terminal in that folder.
4. Create a virtual environment:

   ```powershell
   py -3.12 -m venv .venv
   ```

   If the Python launcher does not recognize `-3.12`, use `python -m venv .venv`.

5. Activate it:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, open Command Prompt and run `.venv\Scripts\activate.bat`.

6. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

7. Start the server:

   ```powershell
   python app.py
   ```

8. Open `http://127.0.0.1:5000` in your browser. Keep the terminal open while using the app.

Alternatively, double-click `run_windows.bat`; it creates a virtual environment if needed, installs dependencies, and launches the app.

## API endpoints

- `GET /` — dashboard
- `POST /predict` — run category analysis using form fields `location` and `year`
- `GET /api/summary` — dataset overview and category counts
- `GET /api/records?location=Ahmedabad&year=2018&limit=100` — filtered JSON records (limit is capped at 500)
- `GET /download?location=Ahmedabad&year=2018` — download filtered CSV; omit filters to download all cleaned rows
- `GET /health` — application health status

Example: open `http://127.0.0.1:5000/api/summary` after starting the app to check that the data loaded.

## Dataset compatibility

The application prefers `crime1_data.xlsx`, then falls back to `crime_data.csv`. It normalizes common header variants such as `City`/`Location`, `Crime Type`/`Type`, and population headers that include units (for example, `Population (in Lakhs) (2011)+`). The `Year`, location, and category fields are required; `Population` and `Crime Rate` are optional. Incomplete rows are excluded and counted in the dashboard.

## Model notes

- Random Forest and Extra Trees classify the supplied category labels from year, location, and population.
- If enough numeric `Crime Rate` values exist, a separate Random Forest regressor estimates that field.
- Accuracy and weighted F1 use a random hold-out split. These metrics are not a future-year benchmark; data leakage and dataset bias may affect them.
- Requests outside the dataset's year range are extrapolations and should be treated cautiously.
