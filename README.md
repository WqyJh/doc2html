# doc2html

Convert document file to html and publish it to github pages.

Why convert to html?
For me, I prefer to read technology documents with web browser where I can read e-books like
reading blogs, easier to zoom, copy, etc.

How it works?
1. Use `ebook-convert` provided by calibre to convert source document to `.htmlz` format.
2. Use `unar` to unarchive the `.htmlz` to web files.
3. Use `git` to create a local git repo and commit web files.
4. Use `hub` to create a remote repo on github.
5. Use `git` to push local files to remote `gh-pages` branch.
6. Wait a moment then read it on `https://<username>.github.io/<repo>/`


## Requirements

- Python >= 3.6
- pip
- pipenv
- calibre
- unar
- git
- [hub](https://github.com/github/hub)


## Supported formats

Support all formats supported by calibre.

## Usage

```bash
./doc2html.py <doc_path> <username>/<repository>
```

Convert `a.epub` and publish it to my github repository `book-a`,
which would be created as private repository.
If you want to deploy to public repository just add `--public` flag.
```bash
./doc2html.py /path/to/a.epub WqyJh/book-a
```

Convert `b.pdf` and publish it.
```bash
./doc2html.py b.pdf WqyJh/book-b
```

If pdf file is scanned, it won't be converted. Because almost all of its contents
are images, which is slow to load and hard to read.

How to determine a pdf file is scanned?
Generally a scanned page only have one image and no text, some of which has a few lines of meta text.
Define a `--pdf-threshold (default:100)`, if the number of characters are less than it, then the page
is treat as scanned.
Define a `--pdf-rate (default:0.6)`, if the rate of text pages over total pages is less than it,
then the pdf document is treat as scanned.

If you still want to convert the scanned pdf, use `--pdf-force` switch.
```bash
./doc2html.py --pdf-force c.pdf WqyJh/book-c
```
