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

The NLTK data files (tokenizer and stopwords) are downloaded automatically the first time the summarizer runs, so the first run needs an internet connection.


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
* `textrank` - builds TF-IDF vectors from the cleaned words of each sentence, measures the cosine similarity between every pair of sentences, and runs PageRank on the resulting graph. Sentences that are similar to many other sentences score highest.

The two methods often agree but can differ. On `article_long.txt`, for example, both choose the same two sentences, and differ on the third: `frequency` picks a survey sentence, while `textrank` picks a sentence that adds the shop owners' opposing view.


## How it works

Every summary goes through one pipeline, `summarizer/pipeline.py`. The command line (`main.py`) uses it, and so can any other front end, such as a web app.

1. **Load** - `data_loader.py` reads a file or folder into articles.
2. **Validate** - `validation.py` checks the text, `num_sentences` and `method`.
3. **Preprocess** - `preprocessing.py` strips URLs, normalizes whitespace, splits headlines off, splits sentences and tokenizes (lowercase, stopwords and non-alphabetic tokens removed).
4. **Score** - `summarizer.py` scores each sentence with `frequency` or `textrank`.
5. **Select** - the top sentences are kept and returned in their original order.

### Using it from Python

`summarize_text` summarizes one string. `summarize_path` summarizes a file or folder and returns one `SummaryResult` per article, with `summary` set, or `error` set if that article failed validation (the rest still run).

    from summarizer.pipeline import summarize_text, summarize_path

    summary = summarize_text(text, num_sentences=3, method="textrank")

    for result in summarize_path("data/samples", num_sentences=2):
        print(result.title, result.ok, result.summary or result.error)

### Project layout

* `main.py` - command line front end.
* `summarizer/pipeline.py` - the single entry point (load, validate, summarize).
* `summarizer/summarizer.py` - `TextSummarizer` with the frequency and TextRank scoring.
* `summarizer/preprocessing.py` - cleaning, headline handling, sentence splitting, tokenizing.
* `summarizer/validation.py` - input checks and `InvalidInputError`.
* `summarizer/data_loader.py` - `.txt`, `.md`, `.csv` and `.json` loading.
* `data/samples/` - the hand-written sample articles.
* `tests/` - the automated tests.


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
* **Ties** - if every sentence gets the same score (for example a text made only of stopwords, sentences that share no words, or identical sentences), the first sentences are returned. `textrank` also falls back to equal scores if PageRank fails to converge.
* **Asking for more sentences than exist** - if `num_sentences` is larger than the number of sentences, the whole text is returned.
* **Odd whitespace** - tabs, repeated spaces and blank lines are cleaned up in the output.
* **Headlines** - a line counts as a headline if it has 12 words or fewer, does not end in sentence punctuation (. ! ? or a closing quote), and the next line starts with a capital letter. Headlines are split off and never chosen for the summary.

### Known limits of headline handling

* A hard-wrapped line whose next line continues with a capitalized word (such as a proper noun) can be mistaken for a headline.
* If a text with a headline has `num_sentences` or fewer real sentences, it is returned as is, without the headline.
* The headline must be followed by a newline to be detected.


## Testing

Run all tests from the project folder with `python -m pytest -q`. There are 118 tests. They cover validation, data loading, both scoring methods, edge cases, headline handling and the command line. The end-to-end tests in `tests/test_pipeline_end_to_end.py` run real files through the whole pipeline and through `main.py` as a subprocess.


## Progress

Done so far:

* Data and configuration: sample data, data loader, input validation, tests (Day 4).
* Core features: TextRank, headline handling, method option on the command line, edge-case tests (Day 5).
* Integration (Day 6): one shared pipeline that the command line now uses, end-to-end tests, faster preprocessing (the stopword list is loaded once instead of for every sentence), and cleanup of an unused `spacy` requirement and an outdated TODO. `numpy` is now listed in `requirements.txt` because the code imports it directly.

Planned next:

* Week 1 review.
* A small web demo (probably Streamlit) built on the same pipeline, then the demo video.
