import sys
import fitz

def convert_pdf_to_md(pdf_path, output_md_path, max_pages=None):
    doc = fitz.open(pdf_path)
    num_pages = len(doc) if not max_pages else int(max_pages)

    with open(output_md_path, "w", encoding="utf-8") as out:
        out.write(f"# {pdf_path} (RAG Markdown)\n\n")

        for page_num in range(num_pages):
            page = doc[page_num]
            text = page.get_text("text")

            lines = text.split('\n')
            out.write(f"\n## Page {page_num + 1}\n\n")

            in_code_block = False
            for raw_line in lines:
                line = raw_line.strip()
                if not line: continue

                is_code = any(line.startswith(token) for token in ["//", "#property", "#define", "{", "}", "void ", "int ", "double ", "string ", "bool ", "class ", "public:", "private:", "protected:", "struct "])

                if is_code:
                    if not in_code_block:
                        out.write("\n```cpp\n")
                        in_code_block = True
                    out.write(f"{raw_line}\n")
                elif in_code_block and (raw_line.startswith(" ") or line.endswith(";") or line.endswith(",")):
                    out.write(f"{raw_line}\n")
                else:
                    if in_code_block:
                        out.write("```\n\n")
                        in_code_block = False
                    out.write(f"{line}\n")

            if in_code_block:
                out.write("```\n\n")

    doc.close()
    print(f"Sikeresen konvertálva: {output_md_path}")

if __name__ == "__main__":
    convert_pdf_to_md(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
