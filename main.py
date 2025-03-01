import time
import random
import sys
import json
import jplookup

def main():
    USE_PROMPT = True
    AGGRESSIVENESS = 5

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
            print(len(word_info))
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
        for i, term in enumerate(terms):
            try:
                sleep_length = random.uniform(AGGRESSIVENESS * 0.5, AGGRESSIVENESS * 1.5)
                time.sleep(sleep_length)
                word_info = jplookup.scrape(term, sleep_seconds=sleep_length)
                
                
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
            """except Exception as e:
                print(f"################################\nEXCEPTION {e} from term {term}\n################################\n")
                exceptionals.append(term)
            """

        with open("exceptionals.txt", "w", encoding="utf-8") as out_file:
            for x in exceptionals:
                out_file.write(x + "\n")

        with open("unfound.txt", "w", encoding="utf-8") as out_file:
            for u in unfound:
                out_file.write(u + "\n")

        # Save the dictionary to a file
        with open("jp-data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    main()