from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import sys

def make_ascii(img_path, out_cols=60, char_aspect=0.5, crop_box=None,
                gamma=1.0, contrast=1.3, invert=False, ramp=None,
                white_cut=1.0, black_floor=0.0):
    im = Image.open(img_path).convert('L')
    if crop_box:
        im = im.crop(crop_box)
    w, h = im.size
    out_rows = int((h / w) * out_cols * char_aspect)
    im_small = im.resize((out_cols, out_rows), Image.LANCZOS)

    # boost contrast a bit for a more graphic look
    im_small = ImageEnhance.Contrast(im_small).enhance(contrast)

    if ramp is None:
        ramp = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    if invert:
        ramp = ramp[::-1]
    n = len(ramp) - 1

    lines = []
    for y in range(out_rows):
        row_chars = []
        for x in range(out_cols):
            p = im_small.getpixel((x, y)) / 255.0
            if p >= white_cut:
                row_chars.append(ramp[0])
                continue
            p = max(0.0, min(1.0, (p - black_floor) / max(1e-6, (white_cut - black_floor))))
            idx = int((1 - p) ** gamma * n)
            idx = max(0, min(n, idx))
            row_chars.append(ramp[idx])
        lines.append(''.join(row_chars))
    return lines

if __name__ == '__main__':
    lines = make_ascii('selfie.jpg', out_cols=70, char_aspect=0.52,
                        crop_box=(300, 150, 3464-300, 3200))
    print('\n'.join(lines))
    print(len(lines), 'rows x', len(lines[0]), 'cols')
