# jplookup
jplookup is a Python tool designed to scrape pitch accent, phonetic pronunciation, definitions and example sentences from Wiktionary and turn them into straight-forward flashcards for Anki.
![oniisan](example-outputs/oniisan-sample.png)

## Features
### Pitch Accent
Anki cards made with jplookup can mark the pitch accent.
This will put a solid dot above the mora that will have a high pitch that's then followed by a mora with a low pitch.
![oriru](example-outputs/oriru-sample.png)

When a noted high pitch is sustained due to being part of a diagraph and/or has a lengthening vowel, then CSS is used to render a line indicating this.
![suiyoobi](example-outputs/suiyoobi-sample.png)

### Scrapes Japanese word data
Retrieves detailed word information from Wiktionary.

`jplookup.scrape("猫")` returns a list of dictionary objects.
The very first dictionary in the list contains the primary results:
![neko](example-outputs/neko-sample.png)

The rest of the list may provide further dictionaries, which are gathered from page redirects whose contents could not be linked back to the primary results dictionary through mutual matching components.

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
