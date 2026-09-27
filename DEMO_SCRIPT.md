DEMO VIDEO SCRIPT - Text Summarizer (Day 23)
=============================================

GOAL: Showcase features and usage. Keep it concise, narrate what you click.

SECTION 1: Intro (10-15s)
- Project name, one line: "Python text summarizer, frequency + TextRank based"
- Mention: CLI tool, Flask API, web UI, deployed live on Render

SECTION 2: Cold start / NLTK warm-up (IMPORTANT - record this FIRST)
- Before recording, hit the live URL once, then wait 15+ min with no traffic
  so Render's free-tier instance spins down.
- On camera: open the live URL fresh, show the first request taking longer
  (NLTK data + instance cold start). Call this out verbally: "first request
  after idle takes longer due to cold start and NLTK data warm-up, this is
  a known free-tier tradeoff."
- This directly covers backlog item 3 from Day 17 user testing.

SECTION 3: Web UI walkthrough
- Paste a sample article/paragraph into the homepage form
- Submit, show summary returned
- Show a short input that fails validation (under MIN_WORDS) to demonstrate
  error handling in the UI

SECTION 4: API usage
- Show POST /summarize via curl or Postman with a valid payload -> 200
- Show a bad payload (e.g. unhashable/malformed) -> 400, not 500
- Show GET /health -> 200

SECTION 5: CLI usage
- Run main.py against a sample text file
- Run it in batch mode against multiple files, show "Skipped" lines grouped
  at the end for any invalid ones

SECTION 6: Logging (brief)
- Open logs/app.log, show a couple of lines: health check entries and a
  timed summarize success line with input_chars and elapsed_ms

SECTION 7: Wrap-up (10s)
- Mention deployment: Render free tier, gunicorn, live URL
- Mention test count: 240 tests passing
- Thank you / end

RECORDING ORDER NOTE:
Record Section 2 (cold start) FIRST, before anything else touches the live
URL, or the warm-up delay will not reproduce.

POST-RECORDING TODO:
- Upload video, get shareable link
- Final submission = repo link + demo URL + demo video link
