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

## Known gap

* Days 8-12 were completed (Streamlit demo, Flask API, error handling,
  dataset slice, deployment) but not logged here day-by-day yet. To be
  backfilled from git log.

## Week 2 plan (tentative, to be adjusted to the official task list)

Goal: a working online demo and a demo video.

* Day 8: install Streamlit and build a small app on summarize_text and summarize_path; add streamlit to requirements.txt.
* Day 9: clear error when the NLTK download fails; test for tie order; minimum token count in the frequency method.
* Day 10: argparse for the command line; document the folder and file failure behavior.
* Day 11: add a small public dataset slice (BBC News or CNN/DailyMail) with source and license documented, and check the summaries on it.
* Day 12: deploy the app on a free host and test it there.
* Day 13: record the demo video and add the demo URL to the README.
* Day 14: Week 2 review and final checks.

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
