from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates = [
            "/usr/share/fonts/TTF/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/TTF/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/TTF/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/TTF/LiberationSerif-Regular.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf",
        ]

    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def _make_default_background(size=(1200, 628)) -> Image.Image:
    """
    Cria um fundo simples (gradiente) para não depender de assets no repo.
    """
    width, height = size
    img = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    top = (18, 22, 28)
    bottom = (60, 50, 70)
    for y in range(height):
        t = y / max(1, height - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    overlay = Image.new("RGBA", size, (0, 0, 0, 90))
    return Image.alpha_composite(img, overlay)


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current_line = words[0]

    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = draw.textbbox((0, 0), test_line, font=font)
        line_width = bbox[2] - bbox[0]

        if line_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    lines.append(current_line)
    return lines


def _get_text_block_height(draw, lines, font, line_spacing: int):
    total_height = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_height = bbox[3] - bbox[1]
        total_height += line_height
        if i < len(lines) - 1:
            total_height += line_spacing
    return total_height


def _draw_centered_text(
    draw,
    lines,
    font,
    center_x: int,
    start_y: int,
    fill,
    shadow_fill=None,
    shadow_offset=(2, 2),
    line_spacing: int = 12,
):
    y = start_y

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        x = center_x - (width // 2)

        if shadow_fill is not None:
            draw.text(
                (x + shadow_offset[0], y + shadow_offset[1]),
                line,
                font=font,
                fill=shadow_fill,
            )

        draw.text((x, y), line, font=font, fill=fill)
        y += height + line_spacing


def gerar_card(texto: str, autor: str, output: str = "card.png", size=(1200, 628)):
    img = _make_default_background(size=size)

    width, height = img.size
    draw = ImageDraw.Draw(img)

    fonte_texto = _load_font(size=54, bold=False)
    fonte_autor = _load_font(size=34, bold=True)

    margin_x = int(width * 0.10)
    max_text_width = width - (2 * margin_x)

    texto_formatado = f'“{texto}”'
    linhas_texto = _wrap_text(draw, texto_formatado, fonte_texto, max_text_width)
    linhas_autor = [autor]

    spacing_text = 14
    spacing_author = 10
    spacing_between = 36

    text_height = _get_text_block_height(draw, linhas_texto, fonte_texto, spacing_text)
    author_height = _get_text_block_height(draw, linhas_autor, fonte_autor, spacing_author)
    total_height = text_height + spacing_between + author_height

    start_y = (height - total_height) // 2
    center_x = width // 2

    _draw_centered_text(
        draw=draw,
        lines=linhas_texto,
        font=fonte_texto,
        center_x=center_x,
        start_y=start_y,
        fill=(245, 245, 240, 255),
        shadow_fill=(0, 0, 0, 140),
        shadow_offset=(2, 2),
        line_spacing=spacing_text,
    )

    y_author = start_y + text_height + spacing_between

    _draw_centered_text(
        draw=draw,
        lines=linhas_autor,
        font=fonte_autor,
        center_x=center_x,
        start_y=y_author,
        fill=(210, 210, 205, 255),
        shadow_fill=(0, 0, 0, 120),
        shadow_offset=(2, 2),
        line_spacing=spacing_author,
    )

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    img.save(output, format="PNG")
    print(f"Card salvo em: {output}")


if __name__ == "__main__":
    gerar_card(
        texto="A felicidade depende de nós mesmos.",
        autor="Aristóteles",
        output="card_teste.png",
    )

