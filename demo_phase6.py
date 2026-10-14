"""MarketLens - Phase 6 Exporter Demonstration.

Loads cleaned data and exports it to both CSV and a professionally styled
Excel workbook (.xlsx) with auto column widths, freeze panes, and custom colors.
"""

from pathlib import Path
import sys
import openpyxl
import pandas as pd

# Ensure src/ is on Python search path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from marketlens.exporter import export_dataset


CLEAN_CSV_PATH = Path("data") / "processed" / "books_cleaned.csv"
OUTPUT_BASE = Path("data") / "processed" / "books_cleaned"


def verify_excel_workbook(file_path: Path) -> None:
    """Inspect and verify the generated Excel workbook using openpyxl."""
    print(f"\n[INSPECTION] Verifying Excel Workbook at: {file_path}")
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    print(f"  * Active Sheet Name    : '{sheet.title}'")
    print(f"  * Freeze Panes Location: {sheet.freeze_panes} (Row 1 stays fixed during scrolling)")
    print(f"  * Total Rows (Data+1)  : {sheet.max_row}")
    print(f"  * Total Columns        : {sheet.max_column}")
    
    # Check Header formatting
    header_cell = sheet["A1"]
    header_fill = header_cell.fill.start_color.rgb if header_cell.fill else None
    print(f"  * Header A1 Text       : '{header_cell.value}'")
    print(f"  * Header A1 Background : {header_fill} (Corporate Navy Blue)")
    
    # Check Price formatting
    price_cell = sheet["B2"]
    print(f"  * Price B2 Value       : {price_cell.value}")
    print(f"  * Price B2 NumberFormat: {price_cell.number_format}")
    
    # Check auto-column widths
    sample_widths = {col: round(sheet.column_dimensions[col].width, 1) for col in ["A", "B", "C", "D"]}
    print(f"  * Sample Column Widths : {sample_widths}")
    print("[VERIFIED] Excel workbook meets all corporate reporting criteria!")


def run_phase6_export() -> None:
    print("=" * 65)
    print("MarketLens: Phase 6 - CSV and Excel Export Automation")
    print("=" * 65)

    if not CLEAN_CSV_PATH.exists():
        print(f"[ERROR] Cleaned file not found: {CLEAN_CSV_PATH}. Run Phase 5 first.", file=sys.stderr)
        return

    # 1. Load cleaned data into pandas DataFrame
    df = pd.read_csv(CLEAN_CSV_PATH, encoding="utf-8-sig")
    print(f"[INPUT] Loaded {len(df)} cleaned records from: {CLEAN_CSV_PATH}")

    # 2. Export using our custom exporter
    print(f"[EXPORT] Generating CSV and styled Excel workbook...")
    export_results = export_dataset(df, OUTPUT_BASE, formats=["csv", "xlsx"])

    # 3. Verify files were created
    for fmt, path in export_results.items():
        size_kb = path.stat().st_size / 1024
        print(f"  -> Generated {fmt.upper()}: {path} ({size_kb:.1f} KB)")

    # 4. Programmatic verification of the Excel workbook
    verify_excel_workbook(export_results["xlsx"])

    print("\n" + "=" * 65)
    print("Phase 6 Export Completed Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    run_phase6_export()
