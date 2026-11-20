"""Run without Streamlit to verify outputs or prepare draft reports from a client ZIP/folder."""
import argparse
from pathlib import Path
from engine.core import Package,generate
from engine.reports import management_pdf,financial_statements_pdf,xlsx_report

def run(source,out):
    src=Path(source)
    package=Package.from_zip(src.read_bytes()) if src.is_file() and src.suffix.lower()=='.zip' else Package.from_directory(src)
    r=generate(package)
    dest=Path(out);dest.mkdir(parents=True,exist_ok=True)
    (dest/'Management_Accounts_DRAFT.pdf').write_bytes(management_pdf(r))
    (dest/'Unaudited_FS_DRAFT.pdf').write_bytes(financial_statements_pdf(r))
    (dest/'Financial_Workpapers_DRAFT.xlsx').write_bytes(xlsx_report(r))
    (dest/'Client_Input_Package.zip').write_bytes(package.to_zip())
    print(f"Generated draft outputs in {dest}; {len(r['errors'])} blocking error(s), {len(r['warnings'])} review item(s)")
    for e in r['errors']:print('ERROR:',e)
    for w in r['warnings']:print('REVIEW:',w)
    return not bool(r['errors'])

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='Otto report generation engine (draft only)')
    ap.add_argument('--input',default='sample_company',help='Client ZIP or directory')
    ap.add_argument('--output',default='demo_output',help='Output directory')
    opts=ap.parse_args();raise SystemExit(0 if run(opts.input,opts.output) else 1)
