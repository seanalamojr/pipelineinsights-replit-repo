from pathlib import Path

import fitz


source = Path("attached_assets/PipelineInsights_—_Review_of_Checkpoints_7,_8,_9_(v8)_1789738173803.pdf")
output = Path(".agents/outputs/checkpoint-review")
output.mkdir(parents=True, exist_ok=True)

document = fitz.open(source)
for index, page in enumerate(document):
    pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
    pixmap.save(output / f"page-{index + 1:02d}.png")
print(f"rendered {document.page_count} pages to {output}")