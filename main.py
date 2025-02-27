import jplookup

def main():
	word = None
	while True:

		print("Enter a word: ", end="")
		word = input()
		if word.lower() == "exit":
			break

		jplookup.scrape(word)

if __name__ == "__main__":
	main()