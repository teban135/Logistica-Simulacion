  # extract_rmd_images.py
  # -------------------------------------------------
  # Render an R Markdown file and collect all images produced
  # by knitr/rmarkdown (the default “figure‑html” folder).
  # -------------------------------------------------

import os
import shutil
import subprocess
import sys
import argparse
from pathlib import Path

def render_rmd(rmd_path: Path) -> Path:
    """
    Calls `Rscript -e "rmarkdown::render('file.Rmd')"` which creates
    `file.html` and a `file_files/figure-html/` directory with the images.
    Returns the path to the generated HTML file.
    """
    if not rmd_path.is_file():
        sys.exit(f"❌  {rmd_path} does not exist")

    cmd = [
        "Rscript",
        "-e",
        f"rmarkdown::render('{rmd_path.as_posix()}')",
    ]
    print(f"⚙️  Rendering {rmd_path.name} …")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        sys.exit(f"❌  R render failed:\n{result.stderr}")

    # rmarkdown creates <basename>.html in the same folder
    html_path = rmd_path.with_suffix(".html")
    if not html_path.is_file():
        sys.exit("❌  Expected HTML output not found")
    return html_path

def find_figure_dir(rmd_path: Path) -> Path:
    """
    knitr stores figures in `<basename>_files/figure-html/`.
    """
    base = rmd_path.stem
    fig_dir = rmd_path.parent / f"{base}_files" / "figure-html"
    if not fig_dir.is_dir():
        sys.exit(f"❌  Figure directory not found: {fig_dir}")
    return fig_dir

def copy_images(src_dir: Path, dst_dir: Path):
    """Copy .png, .jpg, .jpeg, .svg, .pdf files to the destination."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    copied = 0
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.pdf"):
        for img_path in src_dir.glob(ext):
            shutil.copy2(img_path, dst_dir / img_path.name)
            copied += 1
    if copied == 0:
        print("⚠️  No image files found in the figure directory.")
    else:
        print(f"✅  Copied {copied} image(s) to {dst_dir}")

def main():
    parser = argparse.ArgumentParser(
        description="Render an .Rmd file and extract all generated images."
    )
    parser.add_argument(
        "rmd",
        type=Path,
        help="Path to the .Rmd file (e.g., analisis_entrega3.Rmd)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("extracted_images"),
        help="Directory where images will be saved (default: ./extracted_images)",
    )
    args = parser.parse_args()

    rmd_path = args.rmd.resolve()
    out_dir = args.output.resolve()

    # 1️⃣Render the Rmd → HTML
    html_path = render_rmd(rmd_path)
    print(f"📄  HTML output: {html_path}")

    # 2️⃣Locate the figure‑html folder
    fig_dir = find_figure_dir(rmd_path)
    print(f"📁  Figure directory: {fig_dir}")

    # 3️⃣Copy images to the requested output folder
    copy_images(fig_dir, out_dir)

if __name__ == "__main__":
    main()