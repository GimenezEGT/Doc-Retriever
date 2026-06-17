# Doc-Retriever


<img width="2816" height="1536" alt="DocRetriever" src="https://github.com/user-attachments/assets/aea32b8f-40d2-466f-b261-12411c983c5e" />


A small CLI tool to download a website's documentation, convert the collected HTML into clean Markdown, and merge everything into a single `.md` file.

> Note: The script and flags are written in Portuguese (`--saida`, `--manter`)—this README explains them in English while keeping the exact flag names used by the script.

## Features

- Recursively download a docs site (via `wget`) including page requisites (CSS, images, JS).
- Clean HTML (remove scripts, navs, footers, etc.) and convert the main content to Markdown using BeautifulSoup + markdownify.
- Convert each downloaded HTML page into an intermediate `.md` file and merge them into a single consolidated Markdown file.
- Optionally keeps a temporary working directory for inspection.

## Requirements

- Python 3.8+
- System: `wget` (used for site mirroring)
- Python packages:
  - beautifulsoup4
  - markdownify

Install Python deps with:
```bash
pip install beautifulsoup4 markdownify
```

Ensure `wget` is available on your system (Linux/macOS: usually available; Windows: install via WSL or a package manager).

## Quickstart

1. Clone the repository (or download `doc_scraper.py`):
```bash
git clone https://github.com/GimenezEGT/Doc-Retriever.git
cd Doc-Retriever
```

2. Run the script:
```bash
python doc_scraper.py --url https://example.com/docs --saida consolidated_docs.md
```

3. Optional flags:
- `--tmp <folder>` — temporary folder used to store downloaded HTML and intermediate `.md` files (default: `_tmp_scraper`).
- `--manter` — keep the temporary folder after execution (useful for debugging or inspection).

Example (keep temporary files):
```bash
python doc_scraper.py \
  --url https://console.groq.com/docs \
  --saida groq_doc_completa.md \
  --tmp _tmp_scraper \
  --manter
```

## How it works (high level)

1. Uses `wget` to mirror the documentation site into a local temporary folder.
2. For each saved `.html`, the script:
   - Parses with BeautifulSoup, removes non-content tags (script, style, nav, footer, etc.).
   - Attempts to locate the primary content area (`<main>`, `article`, `div#content`, etc.).
   - Converts the HTML fragment to Markdown with `markdownify`.
3. All converted `.md` files are merged into a single output file. Sections are separated with a header that reflects the original path.

## Output

- The final file is the path you set with `--saida`. Inside you'll find `---` separators and `# SEÇÃO: <path>` headers for each included page.
- If you don't pass `--manter`, the temporary folder is removed automatically at the end.

## Limitations & Tips

- The quality of Markdown depends on the HTML structure of the target site. Some sites may require custom cleanup rules for optimal results.
- `wget` options are conservative (it ignores robots and converts links) but may still miss content loaded dynamically via JavaScript. For JS-heavy sites you may need a headless browser approach.
- The script strips inline links (leaves link text only). If you want to preserve links, edit the `limpar_html_para_markdown` function and remove `strip=["a"]` from the markdownify call.
- The script treats return code 8 from `wget` (some broken links) as acceptable; other non-zero return codes will trigger a warning.

## Contributing

PRs and improvements welcome. Ideas:
- Add optional preserving of links.
- Add a HEADLESS (Selenium/Playwright) mode for JS-rendered content.
- Make output templating configurable.

## License

No license file in the repository currently. Add a LICENSE if you want to set reuse rules (MIT, Apache-2.0, etc.).

## Contact

Created by GimenezEGT — for feature requests or issues, open a GitHub issue in this repo.
