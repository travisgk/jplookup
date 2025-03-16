# jplookup

jplookup is a Python tool designed to scrape Japanese word information from Wiktionary. It prioritizes definition relevancies to provide you with the most useful data. The outputs from the `jplookup.scrape(word)` function can then be used to generate a text file that is compatible with Anki flashcards.

## Features

### Scrapes Japanese word data
Retrieves detailed word information from Wiktionary.

<br>

### Anki Integration 
Exports the data into a text file formatted for Anki flashcards.

<br>

### Handles Terms Linking to Other Pages
When Wiktionary links to a different page for an alternative spelling, then the information gathered from that redirect will be filtered through the original spelling in order to provide the only relevant information. 
- "撮る" redirects to the Wiktionary page for "とる" and grabs any definitions that are either specified as fitting with "撮る" or definitions with no context/kanji specification at all.
- "取る" redirects to the Wiktionary page for "とる" and grabs any definitions that are either specified as fitting with "取る" or definitions with no context/kanji specification at all.
- "とる" (the hiragana directly) goes to the Wiktionary page for "とる" and grabs all definitions regardless of context specification.
<br>

## Installation

Clone the repository and install the required dependencies:

```bash
git clone https://github.com/travisgk/jplookup.git
cd jplookup
pip install -r requirements.txt
```
