def extract_data(layout: dict):
	e_keys = list(layout.keys())
	e_keys.sort(key=lambda x: int(x[1:]))  # sorts for safety.
	
	for key in e_keys:
		print(layout[key])

	#print(e_keys)