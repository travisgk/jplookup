import time
import random
import requests
import sys
import json
import jplookup


def main():

    MODE = "all"
    USE_PROMPT = False

    AGGRESSIVENESS = 8

    if MODE == "testing":
        for i, c in enumerate(
            [
                "これ",
                "どうして",
                # "中",
                # "多い",
                # "曇る",
                # "お兄さん",
            ]
        ):
            time.sleep(AGGRESSIVENESS)
            word_info = jplookup.scrape(c, sleep_seconds=5)
            with open(f"out-data-{i}.json", "w", encoding="utf-8") as json_file:
                json.dump(word_info[0], json_file, indent=4, ensure_ascii=False)
            print(word_info[0], end="\n\n\n\n\n\n\n\n\n\n")

    elif MODE == "prompt":
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

    elif MODE == "all":
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
                word_info = jplookup.scrape(term, sleep_seconds=8)

                if len(word_info) > 0:
                    percent_done = int(i / len(terms) * 100)
                    print(f"\n\n{percent_done:> 2d}% {term}:")
                    data[term] = word_info

                    print(word_info[0])
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
                else:
                    print(
                        f"################################\nEXCEPTION {e} from term {term}\n################################\n"
                    )
                    exceptionals.append(term)
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


if __name__ == "__main__":
    main()
