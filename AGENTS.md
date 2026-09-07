# FastLMS repository guidance

## README product media

- Embed only the current `static/fastlearn-demo.gif` walkthrough in `README.md`.
- Link individual Playwright screenshots instead of embedding them as competing walkthroughs.

## FastLearn platform guide

- Keep `docs/fastlearn_platform_guide.md` as the content source and regenerate the PDF with `python scripts/build_platform_guide.py`.
- The PDF is A4 landscape. Every page uses two columns separated by a vertical rule: explanatory copy on the left and a relevant screenshot on the right.
- The cover has one visible title and a product screenshot. The next page is a concise, high-level contents page.
- Do not add process notes, edition lists, screenshot-review notes, or similar production metadata to the presentation unless explicitly requested.
- Do not accept clipped content, blank columns, sparse chapter-divider pages, or excessive empty space. Render every PDF page to a contact sheet and inspect the cover and densest pages at full resolution before committing.
- Commit the Markdown, CSS, builder, generated PDF, and new screenshot assets together.
