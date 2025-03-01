import time
import random
import sys
import json
import jplookup

def main():
    USE_PROMPT = False
    AGGRESSIVENESS = 3

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
        for i, term in enumerate(terms[:15]):
            try:
                word_info = jplookup.scrape(term)
                time.sleep(random.uniform(AGGRESSIVENESS * 0.5, AGGRESSIVENESS * 1.5))
                
                if len(word_info) > 0:
                    print(f"\n\n{term}:")
                    data[term] = word_info

                    print("[")
                    for entry in word_info:
                        print("\t{")
                        for ety_key in entry.keys():
                            print(f'\t\t"{ety_key}": {{')
                            data = entry[ety_key]
                            for d_key in data.keys():
                                print(f"\t\t\t{d_key}: {data[d_key]}")
                            print("\t\t},")
                        print("\t},")

                    #print(f"\n\n{word_info}")
                    #percent_done = int(i / len(terms) * 100)

                    print("]")
                    #print(f"{percent_done}% {term}")
                else:
                    unfound.append(term)
            except KeyboardInterrupt:
                print("Keyboard interrupt received, exiting gracefully.")
                sys.exit(0)
            except Exception as e:
                unfound.append(term)

        with open("unfound.txt", "w", encoding="utf-8") as out_file:
            for u in unfound:
                out_file.write(u + "\n")

        # Save the dictionary to a file
        with open("jp-data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    main()