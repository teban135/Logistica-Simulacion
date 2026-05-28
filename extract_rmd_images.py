# extract_rmd_images.py
# -------------------------------------------------
# Renderiza un archivo R Markdown y recolecta todas las imágenes producidas
# por knitr/rmarkdown (carpeta “figure‑html”).
# -------------------------------------------------

import os
import shutil
import subprocess
import sys
import argparse
from pathlib import Path

def render_rmd(rmd_path: Path) -> Path:
    """
    Llama a `Rscript -e "rmarkdown::render('file.Rmd', clean=FALSE)"` que crea
    `file.html` y una carpeta `file_files/figure-html/` con las imágenes.
    Devuelve la ruta al HTML generado.
    """
    if not rmd_path.is_file():
        sys.exit(f"❌  {rmd_path} does not exist")

    cmd = [
        "Rscript",
        "-e",
        f"rmarkdown::render('{rmd_path.as_posix()}', clean=FALSE)",
    ]
    print(f"⚙️  Rendering {rmd_path.name} …")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        sys.exit(f"❌  R render failed:\n{result.stderr}")

    html_path = rmd_path.with_suffix(".html")
    if not html_path.is_file():
        sys.exit("❌  Expected HTML output not found")
    return html_path

def find_figure_dir(rmd_path: Path) -> Path:
    """
    Busca la carpeta de figuras generada por knitr.
    Normalmente es `<basename>_files/figure-html/`, pero si no está allí,
    se busca recursivamente en subdirectorios.
    """
    base = rmd_path.stem
    expected = rmd_path.parent / f"{base}_files" / "figure-html"
    if expected.is_dir():
        return expected

    # búsqueda recursiva en todo el proyecto
    candidates = list(rmd_path.parent.rglob("figure-html"))
    if not candidates:
        sys.exit(f"❌  Figure directory not found for {base}")
    return candidates[0]

def copy_images(src_dir: Path, dst_dir: Path):
    """Copia archivos de imagen al destino."""
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

    # 1️⃣ Renderizar el Rmd → HTML
    html_path = render_rmd(rmd_path)
    print(f"📄  HTML output: {html_path}")

    # 2️⃣ Localizar la carpeta de figuras
    fig_dir = find_figure_dir(rmd_path)
    print(f"📁  Figure directory: {fig_dir}")

    # 3️⃣ Copiar imágenes al directorio de salida
    copy_images(fig_dir, out_dir)

if __name__ == "__main__":
    main()
