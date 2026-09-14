"""
Générateur d'icône Windows haute définition (.ico multi-résolutions) pour OSBuilder-Win.
Crée une icône professionnelle combinant le logo Windows moderne et le symbole de déploiement OS.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter


def create_app_icon(output_path: Path):
    size = 512  # Haute résolution avec supersampling 2x
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Fond carré aux coins arrondis (Dark Obsidian)
    pad = 28
    radius = 110
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=(13, 16, 24, 255),
        outline=(0, 210, 255, 230),
        width=12
    )

    # 2. Lueur néon subtile intérieure
    draw.rounded_rectangle(
        [pad + 10, pad + 10, size - pad - 10, size - pad - 10],
        radius=radius - 8,
        outline=(0, 114, 255, 90),
        width=6
    )

    # 3. Les 4 quadrants Windows stylisés
    # Centre : 256, 256
    gap = 22
    cx, cy = size // 2, size // 2
    w_size = 140
    rad_quad = 20

    # Quadrant Haut-Gauche (Cyan clair)
    draw.rounded_rectangle(
        [cx - gap // 2 - w_size, cy - gap // 2 - w_size, cx - gap // 2, cy - gap // 2],
        radius=rad_quad,
        fill=(0, 210, 255, 255)
    )

    # Quadrant Haut-Droit (Bleu électrique)
    draw.rounded_rectangle(
        [cx + gap // 2, cy - gap // 2 - w_size, cx + gap // 2 + w_size, cy - gap // 2],
        radius=rad_quad,
        fill=(0, 140, 255, 255)
    )

    # Quadrant Bas-Gauche (Bleu royal)
    draw.rounded_rectangle(
        [cx - gap // 2 - w_size, cy + gap // 2, cx - gap // 2, cy + gap // 2 + w_size],
        radius=rad_quad,
        fill=(0, 102, 235, 255)
    )

    # Quadrant Bas-Droit (Vert émeraude / Menthe - Symbole du succès/build)
    draw.rounded_rectangle(
        [cx + gap // 2, cy + gap // 2, cx + gap // 2 + w_size, cy + gap // 2 + w_size],
        radius=rad_quad,
        fill=(0, 230, 118, 255)
    )

    # 4. Élément central : Disque / Noyau de build
    core_rad = 42
    draw.ellipse(
        [cx - core_rad, cy - core_rad, cx + core_rad, cy + core_rad],
        fill=(13, 16, 24, 255),
        outline=(255, 255, 255, 220),
        width=8
    )
    inner_core = 16
    draw.ellipse(
        [cx - inner_core, cy - inner_core, cx + inner_core, cy + inner_core],
        fill=(0, 210, 255, 255)
    )

    # 5. Redimensionnement avec filtre Lanczos (anti-aliasing parfait)
    img_256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    
    # Sauvegarde au format PNG
    png_path = output_path.with_suffix(".png")
    img_256.save(png_path, "PNG")

    # Sauvegarde au format ICO avec toutes les résolutions requises par Windows
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(
        output_path,
        format="ICO",
        sizes=sizes
    )
    print(f"[OK] Icône générée avec succès : {output_path} ({png_path.name})")


if __name__ == "__main__":
    out_ico = Path(__file__).resolve().parent.parent / "app.ico"
    create_app_icon(out_ico)
