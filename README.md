## Project Goals

The goal of this project is to develop a text summarization system that can convert lengthy text into concise and meaningful summaries while preserving the important information.

### Objectives

* Understand the fundamentals of Natural Language Processing (NLP).
* Implement text preprocessing techniques using Python.
* Study extractive summarization techniques such as TextRank and Latent Semantic Analysis (LSA).
* Explore machine learning approaches for text summarization.
* Understand the differences between extractive and abstractive summarization.
* Develop a working text summarization application.
* Evaluate the quality and usefulness of the generated summaries.


## Installation

Python 3.13 was used for development. From the project folder:

* `pip install -r requirements.txt`

The NLTK data files (tokenizer and stopwords) are downloaded automatically the first time the summarizer runs, so the first run needs an internet connection. If the download fails, the summarizer stops with a clear error (see "Error handling" below) instead of failing silently. To install the data by hand, run `python -m nltk.downloader punkt punkt_tab stopwords`.


## Usage

Run the summarizer from the project folder:

`python main.py <file-or-folder> [num_sentences] [method]`

* `<file-or-folder>` - a `.txt`, `.md`, `.csv` or `.json` file, or a folder of them (see "Supported file formats" below).
* `num_sentences` - how many sentences to keep in each summary.
* `method` - `frequency` (the default) or `textrank`. An unknown method prints `Error: Unknown method 'bogus'. Choose from: frequency, textrank.` and exits with code 1.

Examples:

* `python main.py data/samples/article_long.txt 3`
* `python main.py data/samples/article_long.txt 3 textrank`
* `python main.py data/samples 3 textrank`


## Methods

Both methods are extractive: they pick existing sentences from the text and return them in their original order. Nothing is rewritten.

* `frequency` - cleans and tokenizes the text (stopwords are removed), then scores each sentence by the average frequency of its words. Each word's count is divided by the count of the most common word, and the average (not the sum) is used so that long sentences do not win automatically. The highest-scoring sentences are kept.
* `textrank` - builds TF-IDF vectors from the cleaned words of each sentence, measures the cosine similarity between every pair of sentences, and builds a graph with one node per sentence and the similarity as the edge weight (a sentence does not vote for itself). It then runs PageRank with a damping factor of 0.85, at most 100 iterations and a tolerance of 1e-6; these settings are constants at the top of `summarizer/summarizer.py`. Sentences that are similar to many other sentences score highest.

The two methods often agree but can differ. On `article_long.txt`, for example, both choose the same two sentences, and differ on the third: `frequency` picks a survey sentence, while `textrank` picks a sentence that adds the shop owners' opposing view.


## How it works

Every summary goes through one pipeline, `summarizer/pipeline.py`. The command line (`main.py`) uses it, and so can any other front end, such as a web app.

1. **Load** - `data_loader.py` reads a file or folder into articles.
2. **Validate** - `validation.py` checks the text, `num_sentences` and `method`.
3. **Preprocess** - `preprocessing.py` strips URLs, normalizes whitespace, splits headlines off, splits sentences and tokenizes (lowercase, stopwords and non-alphabetic tokens removed).
4. **Score** - `summarizer.py` scores each sentence with `frequency` or `textrank`.
5. **Select** - the top sentences are kept and returned in their original order.

### Using it from Python

`summarize_text` summarizes one string. `summarize_path` summarizes a file or folder and returns one `SummaryResult` per article, with `summary` set, or `error` set if that article failed validation or hit an unexpected error (the rest still run). Missing NLTK data raises `NLTKDataError` and stops the run. `iter_summaries` does the same but yields the results one at a time (see Large datasets below).

    from summarizer.pipeline import summarize_text, summarize_path

    summary = summarize_text(text, num_sentences=3, method="textrank")

    for result in summarize_path("data/samples", num_sentences=2):
        print(result.title, result.ok, result.summary or result.error)

### Project layout

* `main.py` - command line front end.
* `app.py` - Flask web API (`/health` and `/summarize`).
* `summarizer/pipeline.py` - the single entry point (load, validate, summarize), as a list or one result at a time.
* `summarizer/summarizer.py` - `TextSummarizer` with the frequency and TextRank scoring.
* `summarizer/preprocessing.py` - cleaning, headline handling, sentence splitting, tokenizing, and the NLTK data check (`NLTKDataError`).
* `summarizer/validation.py` - input checks and `InvalidInputError`.
* `summarizer/data_loader.py` - `.txt`, `.md`, `.csv` and `.json` loading, as lists or one article at a time.
* `data/samples/` - the hand-written sample articles.
* `tests/` - the automated tests.


## Large datasets

The loader and the pipeline can work one article at a time, so a big file does not have to fit in memory.

* `iter_articles`, `iter_directory` and `iter_path` (in `summarizer/data_loader.py`) and `iter_summaries` (in `summarizer/pipeline.py`) are generators: they yield one article, or one `SummaryResult`, at a time. `load_articles`, `load_directory` and `summarize_path` are the same functions wrapped in `list(...)`.
* A `.csv` file is read row by row, so memory use stays flat however many rows it has. A `.json` file has to be parsed whole (JSON cannot be streamed), although its articles are still handed on one at a time. Use CSV for very large data.
* Paths and options are checked as soon as you call the function (a missing file, an unsupported extension, a bad `num_sentences` or `method`), not when you start reading the results.
* The command line prints each summary as soon as it is ready. The `=== title (source) ===` headers appear only when there is more than one article.
* An invalid article (for example one with fewer than 20 words) is skipped with a message and the rest still run; the exit code is 1 if any article was skipped. A bad row or an unreadable file still stops the run with `Error: ...` and exit code 1, but the summaries finished before that point are printed first.

Example:

    from summarizer.pipeline import iter_summaries

    for result in iter_summaries("data/samples/articles.csv", num_sentences=2):
        print(result.title, result.summary or result.error)


## API

`app.py` is a small Flask app that serves the same pipeline over HTTP (JSON in, JSON out). Start it from the project folder:

    python app.py

It listens on http://127.0.0.1:5000 (set the `PORT` environment variable to use another port). `flask --app app run` works too. This is the development server; use a production WSGI server for a real deployment.

### Endpoints

* `GET /health` - returns `{"status": "ok"}`.
* `POST /summarize` - summarizes one text. The request must be JSON (`Content-Type: application/json`).

Fields of the `POST /summarize` request:

* `text` (required) - a string with at least 20 words and at most 1,000,000 characters.
* `num_sentences` (optional, default 3) - a whole number of at least 1. Strings such as "3", decimals and booleans are rejected.
* `method` (optional, default `frequency`) - `frequency` or `textrank` (case-insensitive).

A successful response (status 200) contains `summary`, `method` (in lowercase), `num_sentences`, `original_words` and `summary_words`.

Example in PowerShell (with the server running in another window):

    $body = @{ text = "Solar power has grown quickly over the last decade. Panels are cheaper and more efficient than they used to be. Many countries now add more solar capacity than any other source."; num_sentences = 2; method = "textrank" } | ConvertTo-Json
    Invoke-RestMethod -Uri http://127.0.0.1:5000/summarize -Method Post -ContentType "application/json" -Body $body

### Errors

Every error is JSON in the form `{"error": "message"}`:

* `400` - the body is not a JSON object, `text` is missing, or `text`, `num_sentences` or `method` fails validation (the message is the same as on the command line).
* `404` and `405` - unknown URL, or the wrong HTTP method (a 405 also sends an `Allow` header).
* `413` - the request body is larger than 5 MB.
* `415` - the request is not sent as `application/json`.
* `500` - an unexpected error. The client only sees a generic message; the details are logged on the server.
* `503` - the NLTK data is missing and could not be downloaded (see "Error handling"). The client only sees a generic message; the details are logged on the server.


## Error handling

Three kinds of problems are handled:

* **Invalid input** - empty or too short text, a bad `num_sentences` or a bad `method` raises `InvalidInputError`. On the command line the article is skipped with a message and the rest still run (the exit code is 1 at the end). The API returns `400`.
* **An unexpected error on one article** - the article is reported with `error` set to `Unexpected <ErrorType>: <message>`, and the rest of the batch still runs. On the command line it is skipped with a message and the exit code is 1 at the end.
* **Missing NLTK data (for example no network)** - `ensure_nltk_data()` tries to download the data, checks again, and raises `NLTKDataError` with a clear message if something is still missing. This stops the whole run, because every article would fail the same way. The command line prints `Error: ...` and exits with code 1 (summaries finished before that point are printed first). The API returns `503` with a generic message and logs the details. A failed check is not cached, so the next call tries the download again and no restart is needed once the network is back.


## Data sources

### Sample data

All articles in `data/samples/` are original, hand-written, news-style text created for this project. They contain no copyrighted material. There are 7 sample articles in total:

* `article_long.txt` - one long article (plain text)
* `article_short.txt` - one short article (plain text)
* `articles.csv` - 3 articles (columns: `id`, `title`, `text`)
* `articles.json` - 2 articles (fields: `id`, `title`, `text`)

No third-party dataset (such as BBC News or CNN/DailyMail) is bundled with this repository. If one is added later, its source URL, license and any redistribution limits will be recorded in this section.

### Supported file formats

The data pipeline lives in `summarizer/data_loader.py`. Files must be UTF-8 (a BOM is fine).

* `.txt` and `.md` - the whole file is one article. The id and title come from the file name.
* `.csv` - one article per row, with a header row. The text column can be named `text`, `content`, `article` or `body`. Optional columns are `id` and `title` (or `headline`). Column names are case-insensitive.
* `.json` - a list of objects, an object with an `"articles"` list, a single object, or a list of plain strings. The same field names apply.

### Input validation

The rules live in `summarizer/validation.py` and run before every summary:

* The text must be a string, not empty, at least 20 words and at most 1,000,000 characters.
* `num_sentences` must be a whole number of at least 1.
* `method` must be `frequency` or `textrank` (case-insensitive).

### Adding your own data

Save your file in `data/samples/` (or any folder) in one of the supported formats. Then summarize a single file with `python main.py data/samples/articles.csv 3`, or a whole folder with `python main.py data/samples 3`.

Folder mode reads every supported file in the folder (subfolders are not included). An article that fails validation, for example one with fewer than 20 words, is skipped with a message and the rest still run.


## Edge cases

* **Empty or too short input** - text that is empty or has fewer than 20 words raises `InvalidInputError`. In folder mode, that article is skipped with a message and the rest still run.
* **Ties** - if every sentence gets the same score (for example a text made only of stopwords, sentences that share no words, or identical sentences), the first sentences are returned. `textrank` also falls back to equal scores if PageRank fails to converge. If only some sentences tie for a place in the summary, the one that appears earlier in the text is kept (covered by tests).
* **Asking for more sentences than exist** - if `num_sentences` is larger than the number of sentences, the whole text is returned.
* **Odd whitespace** - tabs, repeated spaces and blank lines are cleaned up in the output.
* **Headlines** - a line counts as a headline if it has 12 words or fewer, does not end in sentence punctuation (. ! ? or a closing quote), and the next line starts with a capital letter. Headlines are split off and never chosen for the summary.

### Known limits of headline handling

* A hard-wrapped line whose next line continues with a capitalized word (such as a proper noun) can be mistaken for a headline.
* If a text with a headline has `num_sentences` or fewer real sentences, it is returned as is, without the headline.
* The headline must be followed by a newline to be detected.


## Testing

Run all tests from the project folder with `python -m pytest -q`. There are 193 tests. They cover validation, data loading, both scoring methods, the TextRank settings and tie-breaking, edge cases, headline handling, streaming, the command line and the API. The end-to-end tests in `tests/test_pipeline_end_to_end.py` run real files through the whole pipeline and through `main.py` as a subprocess. The tests in `tests/test_streaming_pipeline.py` check that articles and summaries are produced one at a time, including what happens at a bad CSV row. The tests in `tests/test_api.py` use Flask's test client to check every endpoint, status code and error message. The tests in `tests/test_error_handling.py` use a fake NLTK data folder, so no real network is touched, to check missing data, unexpected errors inside a batch, and the command line and API responses.


## Progress

Done so far:

* Data and configuration: sample data, data loader, input validation, tests (Day 4).
* Core features: TextRank, headline handling, method option on the command line, edge-case tests (Day 5).
* Integration (Day 6): one shared pipeline that the command line now uses, end-to-end tests, faster preprocessing (the stopword list is loaded once instead of for every sentence), and cleanup of an unused `spacy` requirement and an outdated TODO. `numpy` is now listed in `requirements.txt` because the code imports it directly.
* Week 1 review (Day 7): reviewed every module and fixed four problems. Hyphenated words are now kept, a URL no longer removes the period that ends its sentence, the command line writes UTF-8 so redirected output cannot crash, and unreadable files give a clear error. The remaining findings and the Week 2 plan are in `PROJECT_LOG.md`.
* TextRank review (Day 8): the PageRank settings (damping factor 0.85, iteration limit, tolerance) are now named constants, and new tests check them, the fallback when PageRank does not converge, and that tied scores keep the earlier sentence.
* Large datasets (Day 9): the loader and the pipeline now stream. `iter_articles`, `iter_directory`, `iter_path` and `iter_summaries` yield one item at a time, CSV files are read row by row, and the command line prints each summary as soon as it is ready. `csv.field_size_limit` is now set once at module level.
* Web API (Day 10): `app.py` is a Flask app with `GET /health` and `POST /summarize`, built on the same pipeline. Bad input returns a JSON error with status 400, and the other errors (404, 405, 413, 415, 500) are JSON too. `flask` is now in `requirements.txt`, and 29 new tests use Flask's test client.
* Error handling (Day 11): missing NLTK data (for example with no network) now raises a clear `NLTKDataError` instead of failing silently, and a failed check is retried on the next call. The command line prints `Error: ...` and exits with code 1, and the API returns a 503 with a generic message. An unexpected error on one article no longer stops a batch: that article is reported and the rest still run. 14 new tests use a fake NLTK data folder.

Planned next:

* A small web demo (probably Streamlit) built on the same pipeline, then the demo video.
