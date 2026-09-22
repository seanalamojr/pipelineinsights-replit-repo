from pathlib import Path

import fitz


source = Path(
    "attached_assets/PipelineInsights_—_Review_of_Checkpoints_4,_5,_6_(v5)_1789693790553.pdf"
)
output = Path(".agents/outputs/checkpoints456-review")
output.mkdir(parents=True, exist_ok=True)

document = fitz.open(source)
for page_number, page in enumerate(document, start=1):
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pixmap.save(output / f"page-{page_number:02d}.png")

print(f"rendered {len(document)} pages to {output}")