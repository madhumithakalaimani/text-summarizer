# Day 17: User Testing and Feedback

Manual user testing of the CLI (main.py) and Flask API (app.py) using the
existing pipeline, to evaluate usability from a first-time user's point of
view. No production code was changed as part of this session; findings
below are logged as backlog items.

## Test setup

Three sample text files (short, long, empty) plus the sample articles
already in tests/sample_articles.py were run through:

* main.py against a single file (frequency method, default sentence count)
* main.py against a single file (frequency method, explicit sentence count)
* main.py against a single file (textrank method)
* main.py against an empty file
* main.py against a whole folder (mixed valid/invalid files)
* Flask API: GET /health
* Flask API: POST /summarize with input below the minimum word count

## Observations

1. Short-input error ("Text is too short (9 words; minimum is 20).") is
   accurate but does not tell the user what to do next (e.g. add more
   text, or lower a --min-words style setting if one existed). Same
   message shape is reused by the API, so this affects both interfaces.
2. Folder batch output interleaves "Skipped ..." lines from files that
   sort earlier alphabetically with the summary block of a later file,
   so skipped files are not visually grouped together. A user scanning
   output for skipped files has to read the whole batch output rather
   than seeing all skips up front.
3. The API's /health endpoint responds quickly and clearly with
   {"status": "ok"}, and /summarize returns a clean 400 with a JSON error
   body for invalid input rather than a 500 - this matches the Day 13
   error-handling work and reads well from a client's perspective.
4. First request to the Flask server (or first CLI run in a fresh
   process) has a noticeable startup delay, most likely NLTK data /
   model loading. Not a correctness issue, but worth calling out for the
   demo video so the delay does not look like the app is frozen.
5. TextRank and frequency summaries were both coherent on the sample
   long-article text; no factual or ordering problems observed in this
   session.

## Backlog items from this feedback (not yet implemented)

* Improve short-input error message to suggest a next step for the user.
* Group "Skipped" lines separately from successful summaries in batch
  (folder) output, e.g. print all skips first or as a trailing summary.
* Note the first-request warm-up delay in the demo video script so it is
  not mistaken for a hang.
