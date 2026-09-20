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
