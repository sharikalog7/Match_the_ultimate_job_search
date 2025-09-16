# h1b_loader.py
import pandas as pd
from typing import Optional

class H1BLookup:
    def __init__(self, csv_path: str):
        """
        csv_path: path to a CSV with at minimum a column 'employer_name' and optionally year/case_count
        """
        self.df = pd.read_csv(csv_path)
        # normalize employer name column
        self.df['employer_name_norm'] = self.df['employer_name'].str.lower().str.strip()

    def company_history(self, company_name: str) -> Optional[pd.Series]:
        if not company_name or not isinstance(company_name, str):
            return None
        n = company_name.lower().strip()
        matched = self.df[self.df['employer_name_norm'].str.contains(n, na=False)]
        if matched.empty:
            # Try simple fuzzy-ish check: substring
            matched = self.df[self.df['employer_name_norm'].str.contains(n.split()[0], na=False)]
        if matched.empty:
            return None
        # Return aggregated info
        total_cases = matched['case_count'].sum() if 'case_count' in matched.columns else None
        years = matched['year'].unique().tolist() if 'year' in matched.columns else None
        return {
            "rows_found": len(matched),
            "total_cases": int(total_cases) if total_cases is not None else None,
            "years": years
        }
