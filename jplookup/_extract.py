from ._cleanstr import remove_tags, extract_tag_contents

def extract_data(layout: dict):
	e_keys = list(layout.keys())
	e_keys.sort(key=lambda x: int(x[1:]))  # sorts for safety.
	
	data = {}
	print(layout)

	for key in e_keys:
		#print(layout[key])
		data[key] = {"pronunciations": [], "definitions": []}

		e = layout[key]
		print("\n\n")

		results = []
		results.extend([(p.sourceline, p) for p in e["pronunciation-headers"]])
		results.extend([(s.sourceline, s) for s in e["speech-headers"]])
		results.sort(key=lambda x: x[0])
		to_end_line = {
			results[i][1]: (
				results[i + 1][0] if i < len(results) - 1 else e["end-line-num"]
			)
			for i in range(len(results))
		}

		for p_header in e["pronunciation-headers"]:
			#print(e["p-end-line-nums"])
			uls = p_header.find_all_next("ul")
			#print(ul)

			# print(p_end_line)
			for ul in uls:
				ul_text = ul.get_text()
				if ul.sourceline < to_end_line[p_header]: #and "IPA" in ul_text:
					contents = extract_tag_contents(str(ul), "li")
					contents = [remove_tags(c) for c in contents]
					print(f"{key}\t{contents}")

	#print(e_keys)