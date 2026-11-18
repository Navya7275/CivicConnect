# Project report

`CivicConnect_Project_Report.docx` is the major-project report in the ITM
thesis format. The PDF beside it is a render of that same file, for reading
without Word.

Both are generated, not hand-written, so that the numbers in them can be
regenerated when the evaluation is re-run rather than edited by hand in two
places and drifting apart.

## Rebuilding

```bash
pip install matplotlib python-docx
python docs/report/build_figures.py   # writes docs/report/figures/*.png
python docs/report/build_report.py    # writes the .docx beside this file
```

`build_figures.py` reads the corpus straight out of
`data/ingestion/seed_chunks.json` and `seed_schemes.json`, so Figure 2 — the
corpus composition and the chunk-length histogram — always matches whatever
the corpus currently holds.

To refresh the PDF:

```bash
soffice --headless --convert-to pdf --outdir docs/report \
        docs/report/CivicConnect_Project_Report.docx
```

## What is NOT derived automatically

The retrieval figures — Tables 7 and 8, and Figures 6, 7 and 8 — are written
into `build_figures.py` and `build_report.py` as literals. They come from runs
of `python -m data.eval.run_eval`, which needs the index built and the
embedding model downloadable, so they cannot be recomputed at document-build
time.

**Re-run the evaluation and check those numbers before submitting.** If any of
them moved, edit the literals in both scripts and rebuild. The conditions they
were measured under are stated in the report itself and must be updated with
them: 963 indexed chunks, 109 answerable questions, recall@10, fusion constant
k = 5 with the dense arm weighted 3.0.

## Placeholders in the document

Roll numbers for three of the four students, the guide's name, and the
university logo on the title page are left blank in `build_report.py`. Fill
them in the script and rebuild, rather than in the .docx, or the next rebuild
will drop them.
