# HR Dataset Dashboard

This project turns the HR dataset into an interactive workforce dashboard using Streamlit.

## Project layout

- `src/` – dashboard application code
- `data/processed/` – cleaned HR dataset used by the app
- `data/raw/` – original raw HR data
- `notebooks/` – analysis notebook
- `reports/` – exported Tableau/report assets

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

The dashboard opens in your browser and includes filters for department, status, business unit, and gender, plus key workforce metrics and charts.
