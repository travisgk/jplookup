import time
import random
import requests
import sys
import json
import jplookup


def main():

    USE_PROMPT = False

    AGGRESSIVENESS = 6

    """
    for i, c in enumerate(
        [
            "炎",
            "矢",
        ]
    ):
        time.sleep(AGGRESSIVENESS)
        word_info = jplookup.scrape(c, sleep_seconds=5)
        with open(f"out-data-{i}.json", "w", encoding="utf-8") as json_file:
            json.dump(word_info[0], json_file, indent=4, ensure_ascii=False)
        print(word_info[0], end="\n\n\n\n\n\n\n\n\n\n")
    
    """

    if USE_PROMPT:
        word = None
        while True:
            print("Enter a word: ", end="")
            word = input()
            if len(word) == 0:
                print("Please enter a word.")
                continue

            if word.lower() == "exit":
                break

            word_info = jplookup.scrape(word)
            # print(len(word_info))
            for info in word_info:
                print(info)

    else:
        terms = []
        with open("n5.txt", "r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if clean_line not in terms:
                    terms.append(clean_line)

        data = {}

        unfound = []
        exceptionals = []
        i = 0
        num_retries = 0
        while i < len(terms):
            term = terms[i]
            try:
                sleep_length = random.uniform(
                    AGGRESSIVENESS * 0.75, AGGRESSIVENESS * 1.5
                )
                time.sleep(sleep_length)
                word_info = jplookup.scrape(term, sleep_seconds=6)

                if len(word_info) > 0:
                    percent_done = int(i / len(terms) * 100)
                    print(f"\n\n{percent_done:> 2d}% {term}:")
                    data[term] = word_info

                    print(word_info)
                else:
                    unfound.append(term)
            except KeyboardInterrupt:
                print("Keyboard interrupt received, exiting gracefully.")
                sys.exit(0)
            except requests.exceptions.HTTPError as e:
                time.sleep(20)  # take a long break.
                print("Whoops. Let's try that again.")
                num_retries += 1
                if num_retries <= 3:
                    continue  # tries again.
            except Exception as e:
                print(
                    f"################################\nEXCEPTION {e} from term {term}\n################################\n"
                )
                exceptionals.append(term)
            i += 1
            num_retries = 0

        with open("exceptionals.txt", "w", encoding="utf-8") as out_file:
            for x in exceptionals:
                out_file.write(x + "\n")

        with open("unfound.txt", "w", encoding="utf-8") as out_file:
            for u in unfound:
                out_file.write(u + "\n")

        # Save the dictionary to a file
        with open("jp-data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    '''

    ###########################
    # loads the .json with the written jplookup info.
    with open("jp-data.json", "r", encoding="utf-8") as f:
        word_info = json.load(f)

    # goes through each term in the .json.
    for key in word_info.keys():
        print(key)

        # looks for the term.
        data = word_info.get(key)
        if data is None or len(data) == 0:
            continue  # skips if term is not in dict.
        
        # looks for the first etymology header.
        data[0]["Etymology 1"]
        for i in range(1, 10):
            etym = data[0].get(f"Etymology {i}")
            if etym is not None:
                data = etym
                break
        else:
            continue

        for part_of_speech in data.keys():
            print(part_of_speech)
            

    # Print formatted JSON
    data = word_info.get("水")
    if len(data) > 0:
        print(data[0]["Etymology 1"])
    """
    '''


if __name__ == "__main__":
    main()
