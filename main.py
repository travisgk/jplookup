import jplookup
import time
import random
import json



def main():
    USE_PROMPT = True


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
            print(word_info)

    else:
        terms = []
        with open("n5.txt", "r", encoding="utf-8") as file:
            for line in file:
                clean_line = line.strip()
                if clean_line not in terms:
                    terms.append(clean_line)

        data = {}

        unfound = []
        for i, term in enumerate(terms[:10]):
            word_info = jplookup.scrape(term)
            time.sleep(random.uniform(1.1, 3.5))
            if len(word_info) > 0:
                data[term] = word_info
                print(f"\n\n{word_info}")
                percent_done = int(i / len(terms) * 100)
                print(f"{percent_done}% {term}")
            else:
                unfound.append(term)

        with open("unfound.txt", "w", encoding="utf-8") as out_file:
            for u in unfound:
                out_file.write(u + "\n")

        # Save the dictionary to a file
        with open("jp-data.json", "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)


if __name__ == "__main__":
    main()