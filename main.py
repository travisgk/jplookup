import json
import os
import jplookup


def main():
    local_dir = os.path.dirname(os.path.abspath(__file__))
    in_dir = os.path.join(local_dir, "example-inputs")
    out_dir = os.path.join(local_dir, "example-outputs")

    '''
    # Sample A creates a tiny Anki deck with only 友情" and "猫".
    print("Creating a small sample deck.")
    results = jplookup.scrape_all(
        words=["友情", "猫"],
        out_path=os.path.join(out_dir, "sample-a-neko.json"),
    )
    for term, word_info in results.items():
        print(f'Here\'s the data for "{term}":')
        print(json.dumps(word_info[0], indent=4, ensure_ascii=False), end="\n\n")
    jplookup.make_cards(
        in_path=os.path.join(out_dir, "sample-a-neko.json"),
        out_path=os.path.join(out_dir, "sample-a-neko-anki.txt"),
    )
    print("Done!", end="\n" * 5)'''

    # Sample B creates a deck of all N5 vocabulary listed in a text file.
    print("Creating a deck of all N5 vocabulary.")
    '''results = jplookup.scrape_all(
        in_path=os.path.join(in_dir, "sample-b-n5.txt"),  # all words in file.
        out_path=os.path.join(out_dir, "sample-b-n5.json"),
    )'''
    jplookup.make_cards(
        in_path=os.path.join(out_dir, "sample-b-n5.json"),
        out_path=os.path.join(out_dir, "sample-b-n5-anki.txt"),
    )


if __name__ == "__main__":
    main()
