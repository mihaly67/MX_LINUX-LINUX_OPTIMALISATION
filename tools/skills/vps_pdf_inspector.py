import sys
import fitz # PyMuPDF

def analyze_pdf(pdf_path, max_pages=15):
    print(f"\\n{'='*50}")
    print(f"📄 ELEMZÉS ALATT: {pdf_path}")
    print(f"{'='*50}")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Hiba a PDF megnyitásakor: {e}")
        return

    print(f"Összes oldal: {len(doc)}")

    font_stats = {}
    code_blocks = []

    # Elemzünk pár oldalt a közepéből, ahol tuti van kód (pl. 20-35. oldal)
    start_page = min(20, len(doc)-1)
    end_page = min(start_page + max_pages, len(doc))

    for i in range(start_page, end_page):
        page = doc[i]

        # 1. Betűtípusok és blokkok kinyerése (dict formátum)
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b['type'] == 0:  # Szöveg blokk
                for l in b["lines"]:
                    for s in l["spans"]:
                        font = s["font"]
                        size = round(s["size"], 1)
                        text = s["text"].strip()
                        if not text: continue

                        key = f"{font} ({size}pt)"
                        if key not in font_stats:
                            font_stats[key] = {"count": 0, "sample": text}
                        font_stats[key]["count"] += len(text)

                        # Próbáljuk detektálni a kódot "Courier", "Mono", "Consolas" stb alapján
                        if "Courier" in font or "Mono" in font or "Consolas" in font or "SourceCodePro" in font:
                            code_blocks.append(text)

    print("\\n🖋️ DETEKTÁLT BETŰTÍPUSOK ÉS MÉRETEK (Statisztika):")
    # Sorbarendezés előfordulás (szöveghossz) alapján
    sorted_fonts = sorted(font_stats.items(), key=lambda x: x[1]["count"], reverse=True)
    for font_key, data in sorted_fonts:
        print(f" - {font_key}: {data['count']} karakter (Minta: '{data['sample'][:30]}...')")

    print(f"\\n💻 DETEKTÁLT 'KÓDGYANÚS' BLOKKOK (Monospace betűtípus alapján): {len(code_blocks)}")
    if code_blocks:
        print("Minta kód:")
        for code in code_blocks[:10]:
            print(f"   > {code}")

    doc.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Használat: python3 vps_pdf_inspector.py <pdf_path>")
        sys.exit(1)
    analyze_pdf(sys.argv[1])
