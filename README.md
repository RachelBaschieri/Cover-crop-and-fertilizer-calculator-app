# Cover Crop and Nutrient Calculator beta

## Run in VS Code

1. Put `app.py`, `requirements.txt`, `templates/`, and `static/` in one project folder.
2. Open that folder in VS Code.
3. Open a terminal and create a virtual environment:
   - Windows: `py -m venv .venv`
   - macOS/Linux: `python3 -m venv .venv`
4. Activate it:
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - macOS/Linux: `source .venv/bin/activate`
5. Install: `python -m pip install -r requirements.txt`
6. Run: `python app.py`
7. Open `http://127.0.0.1:5000`.

## Formula map

- Fraction of acre = sampled ft² / 43,560
- Fresh biomass (lb/ac) = fresh sample weight / fraction of acre
- Dry biomass = fresh biomass × dry matter % / 100
- Total crop N = dry biomass × lab N % / 100
- Crop PAN = total crop N × PAN % / 100
- Nutrient supplied = application rate × material analysis % / 100
- Material cost = application rate × product price
- Cost per lb nutrient = product price / nutrient fraction
- Fuel use = 0.044 × tractor horsepower
- Tractor ownership cost = 0.125 × horsepower
- Field capacity (ac/hr) = speed × width × 0.85 field efficiency / 8.247
- Operation cost ($/ac) = (implement + fuel + tractor + labor hourly costs) / field capacity
- Balance = applied nutrient − recommendation

The workbook output available to this conversion did not expose every original cell expression. The app therefore uses transparent equations derived from the workbook's displayed calculations. Cover-crop PAN uses linear interpolation among the cereal rye + common vetch points visible in the workbook. Compare additional beta cases against Excel before production use.
