import glob
import os

# Prefer pypdf (modern). This script finds the first PDF in the repo root and extracts text.
try:
    from pypdf import PdfReader
except Exception:
    raise SystemExit('pypdf not installed')

pdfs = glob.glob('*.pdf')
if not pdfs:
    raise SystemExit('No PDF found in repo root')

pdf_path = pdfs[0]
reader = PdfReader(pdf_path)

texts = []
for page in reader.pages:
    try:
        texts.append(page.extract_text() or '')
    except Exception:
        texts.append('')

out_dir = os.path.join('docs')
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, 'pdf_requirements.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(texts))

print('Extracted', pdf_path, '->', out_path)
