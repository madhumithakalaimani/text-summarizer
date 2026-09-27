# Project log

## Week 1 (Days 1-7)

### Progress

* Days 1-3: project setup and the first version of the summarizer.
* Day 4 (data and config): sample data, data loader for .txt, .md, .csv and .json, input validation, tests, README "Data sources".
* Day 5 (core features): TextRank next to the frequency baseline, headline handling, a method option on the command line, edge-case tests.
* Day 6 (integration): one shared pipeline (summarizer/pipeline.py) used by main.py, end-to-end tests, stopword list cached, unused spaCy requirement removed.
* Day 7 (review): reviewed every module, fixed four real problems, and logged the rest for Week 2.

End of Week 1: 129 tests passing.

### Challenges and how they were handled

* Headlines were glued to the first sentence after them. Fix: a headline rule (12 words or fewer, no closing punctuation, next line starts with a capital letter) and headlines are never chosen for the summary. The limits of this rule are listed in the README.
* TextRank can have nothing to compare (empty vocabulary, no shared words, PageRank not converging). Fix: return equal scores, so the first sentences win the tie.
* Preprocessing was slow because the stopword list was loaded for every sentence. Fix: load it once and cache it.
* One bad article should not stop a whole folder. Fix: the pipeline records the error for that article and continues with the rest.
* Windows shell problems: work once slipped into a ZIP copy of the project (now the folder is checked at the start of every session), and the command line crashed on some characters when output was redirected (found in the Day 7 review).

### Day 7 review: fixed

* Hyphenated words such as well-known were dropped by the tokenizer. They are now kept (commit 8ec094f).
* Removing a URL also removed the period that ended the sentence, so two sentences merged. The period is now kept (commit 8ec094f).
* The command line crashed with a UnicodeEncodeError when output was redirected and contained characters such as the rupee sign. Output is now written as UTF-8 (commit ac169c8).
* Unreadable files (permission problems, CSV errors) gave raw tracebacks. They now raise DataLoadError with a clear message (commit cb1357b).

### Day 7 review: found and moved to Week 2

* The frequency method can favor very short sentences made of the most common word.
* A failed NLTK download is silent, so a later error is confusing when offline.
* No test pins the rule that tied scores keep the earlier sentence first.
* The command line reads arguments by hand: --help is not supported and extra arguments are ignored.
* One bad file aborts a whole folder run, and one bad row aborts its file. This is by design and should be documented.
* Only InvalidInputError is caught per article, so any other error in one article stops the batch.
* A short line ending in a colon or an ellipsis, followed by a capitalized line, is treated as a headline.
* Small polish: type hints in validation.py, long lines, csv.field_size_limit set on every call, and _pick returns an empty first match even if a later column has text.

## Day 8

Official task: (Week 2 plan) explicit TextRank configuration and algorithm tests.

* Made TextRank settings explicit rather than relying on library defaults,
  and added dedicated algorithm tests to lock in expected behavior
  (commit a758ee8).

## Day 9

Official task: (Week 2 plan) handle larger datasets without memory issues.

* Data loader now streams articles one at a time instead of loading a
  whole dataset into memory at once, so large inputs fit in memory
  (commit d057bb3).

## Day 10

Official task: (Week 2 plan) expose the summarizer as a web API.

* Added a Flask API (app.py) with a GET /health endpoint and a
  POST /summarize endpoint, plus tests for both (commit d0eedf3).

## Day 11

Official task: (Week 2 plan) handle missing NLTK data and unexpected errors.

* Added error handling for missing NLTK data (raises a clear NLTKDataError
  instead of a raw exception) and for unexpected errors more generally
  (commit 241467d).

## Day 12

Official task: (Week 2 plan) direct unit tests for core algorithm behavior.

* Added tests/test_frequency_algorithm.py and tests/test_summarize_inputs.py,
  testing the frequency scoring method and summarize() input handling
  directly rather than only through higher-level tests (commit 6f026b5).

## Day 13

Official task: performance testing of the text summarizer using
benchmarking tools.

* Installed pytest-benchmark and added it to requirements.txt.
* Added tests/test_benchmark_performance.py, benchmarking summarize_text
  for both frequency and textrank methods across short, medium and long
  inputs (base sample text repeated 1x, 5x and 20x).
* Results (mean time): frequency is faster than textrank at every size,
  and the gap widens as input grows (short: ~0.5ms vs ~3.0ms; medium:
  ~2.4ms vs ~5.8ms; long: ~11.1ms vs ~39.7ms). TextRank's graph-based
  ranking scales worse with input size than the frequency count.
* Full suite: 228 tests passing (222 previous + 6 new benchmarks).

## Day 14

Official task: code review and refactor for readability.

* Reviewed the codebase for readability and refactored accordingly
  (commit 83c96c8).

## Day 15

Official task: add advanced features such as summarization of long
documents or multi-document summarization.

* Added summarize_multiple() to summarizer/pipeline.py: joins a list of
  documents into one text and summarizes them together with the existing
  TextSummarizer, so the result can draw sentences from any input document.
* Raises InvalidInputError if the document list is empty; reuses the
  existing validate_method and validate_num_sentences checks.
* Added tests/test_multi_document.py: combining two documents, a single
  document, the empty-list error, and the textrank method.
* Long-document chunking was considered but left for a later day, since it
  needs a merge/re-rank strategy rather than reusing the pipeline directly.
* Full suite: 233 tests passing (229 previous + 4 new).


## Day 16

Official task: optimize performance of the text summarizer using
techniques such as parallel processing or caching.

* Added caching to summarizer/pipeline.py: summarize_text() now checks
  that text is a string (raising InvalidInputError otherwise) and then
  delegates to a new _cached_summarize_text(), which is wrapped in
  functools.lru_cache(maxsize=256). Repeated identical calls (same text,
  num_sentences, method) now return instantly instead of re-running
  NLTK/TF-IDF work.
* The string check happens in summarize_text() rather than inside the
  cached function because lru_cache requires hashable arguments; without
  the check, a non-string text such as a list raised a raw TypeError
  instead of the usual InvalidInputError. Caught by test_api.py during
  this change and fixed by splitting the function in two.
* Added tests/test_caching.py: a repeated call registers a cache hit, a
  cached result matches an uncached result, and a non-string input still
  raises InvalidInputError rather than TypeError.
* Full suite: 236 tests passing (233 previous + 3 new caching tests).

## Day 17

Official task: conduct user testing and gather feedback on the text
summarizer.

* Manually tested main.py (CLI) against short, long, and empty text files,
  the textrank method, and a mixed-content folder batch run; also tested
  the Flask API's /health and /summarize (invalid input) endpoints.
* No production code changed. Findings and a backlog of follow-up items
  written up in docs/day17_user_testing.md.
* Key findings: short-input error message could suggest a next step;
  batch-folder output does not group skipped files separately from
  successful summaries; first request has a noticeable NLTK warm-up
  delay worth flagging in the demo video.
* Full suite: 236 tests passing (no change, no code touched).

## Day 18

Official task: fix reported bugs and improve overall user experience.

* Addressed backlog item 1 from docs/day17_user_testing.md: the
  short-input error message in summarizer/validation.py now suggests a
  next step ("Add more text and try again.") in addition to reporting
  the word count and minimum.
* Addressed backlog item 2: main.py's batch (folder) output now prints
  all "Skipped" lines together at the end, after the summaries, instead
  of interleaving them with successful results. Refactored
  _print_result/_print_results into _print_summary, _print_skipped, and
  a slimmer _print_results that collects skipped results and prints them
  as a group.
* Backlog item 3 (NLTK warm-up delay) is a demo-video script note, not a
  code fix; left for when the demo video is scripted.
* Full suite: 236 tests passing (no new tests; existing tests only check
  substrings of the changed messages, so no test changes were needed).

## Day 19

Official task: (Week 2 plan, extended) build a frontend for the API.

* Added a Flask-served HTML/CSS/JS frontend (templates/index.html,
  static/style.css, static/script.js) as a vanilla JS fetch-based UI
  for /summarize, tested working in the browser (commit 0557a7f).

## Day 20

Official task: add monitoring/observability to the running service.

* Added summarizer/logging_config.py with setup_logging(): a rotating
  file handler (logs/app.log, 1MB, 3 backups) plus a console handler.
* app.py now logs health checks and timed summarize success/failure,
  including input_chars and elapsed_ms (commit dd17556).
* Added tests/test_logging.py.

## Day 22

Official task: deploy the text summarizer to production using a cloud
platform (task text named AWS or Google Cloud as examples).

* Chose Render (free tier, no card required) over AWS/GCP: a full AWS or
  GCP setup (IAM, billing account, CLI) was disproportionate for a
  single Flask demo app, and free-tier GCP/AWS still require a card on
  file even when usage stays free.
* app.py: host changed from 127.0.0.1 to 0.0.0.0 so the process accepts
  external connections (commit 1dc1cc0).
* requirements.txt: added gunicorn as the production WSGI server
  (Flask's dev server is not for production use) (commit 1dc1cc0).
* Added render.yaml documenting the build command
  (pip install -r requirements.txt) and start command
  (gunicorn app:app --bind 0.0.0.0:$PORT) (commit 1dc1cc0).
* Deployed via Render dashboard, connected to the GitHub repo, plan set
  to Free. Live at https://text-summarizer-9e4x.onrender.com.
* Verified in production: homepage loads, /health returns
  {"status": "ok"}, and /summarize correctly returns a 3-sentence
  frequency summary for a test paragraph.
* Updated README.md: test count corrected to 240, added Progress entries
  for Days 19-22, added deployment info, updated "Planned next" to
  reference recording the demo video instead of the superseded
  Streamlit-demo plan.
* Full suite: 240 tests passing (no test changes needed; deployment
  config and docs only).

## Day 23

Official task: record a demo video of the deployed application.

* Wrote DEMO_SCRIPT.md as a recording checklist.
* Recorded a ~67s screen-capture demo of the live site (a successful
  summary and the validation error message), with audio.
* Uploaded the video to Google Drive with a shareable "Anyone with the
  link / Viewer" link; the link is now in README.md's new "Demo" section.
* The recording started with the server already warm, so the NLTK
  cold-start delay flagged in Day 17 user testing was not captured on
  camera. Decided to document it as a known limitation in README.md
  rather than record a supplementary clip.
* Full suite: 240 tests passing (no code changed).

## Day 24

Official task: write final README with instructions and examples.

* Added a "Demo" section to README.md: live URL, demo video link, and
  the NLTK cold-start known limitation (see Day 23).
* Updated the Progress section: added the Day 23 entry, and changed
  "Planned next" to point at submitting the project on CodeZoner.
* Full suite: 240 tests passing (docs only, no code changed).

## Day 27

Official task: clean up portfolio and ensure consistency across all projects.

* Added an H1 title ("# Text Summarizer") to the top of README.md, matching
  the H1 convention already used in PROJECT_LOG.md.
* Added a LICENSE file (MIT, 2026, Madhumitha Kalaimani) - the repo had no
  license file before this.
* Full suite: 240 tests passing (docs only, no code changed).
* Note: this work was pushed as commit c34ee71 with the message "Day 25:
  add README title, LICENSE file for portfolio consistency" - that label
  is a mistake carried over from miscounting internship days; the work
  described in that commit is this Day 27 task, not Day 25. Recording the
  correct day here since the commit message itself was not amended (no
  force-push, per project rules).
