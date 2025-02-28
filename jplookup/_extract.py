from ._cleanstr import remove_tags, remove_unwanted_html, extract_tag_contents

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
            uls = p_header.find_all_next("ul")
            for ul in uls:
                if ul.sourceline >= to_end_line[p_header]:
                    break

                ul_text = ul.get_text()
                if "IPA" in ul_text:
                    contents = extract_tag_contents(str(ul), "li")
                    contents = [remove_tags(c) for c in contents]
                    # TODO Pronunciation IPA info
                    print(f"{key}\t{contents}")
        

        for s_header in e["speech-headers"]:
            print(s_header)
            headword = None
            headword_span = s_header.find_next("span", class_="headword-line")
            if headword_span is not None:
                headword = str(headword_span).strip()
                period_index = headword.find("•")
                if period_index >= 0:
                    headword = headword[:period_index].strip()
                headword = remove_tags(headword).replace("\u0020", "")
                print("\t" + headword)
            else:
                continue

            ol = headword_span.find_next("ol")
            if ol is not None:
                ol_str = str(ol)
                li_contents = extract_tag_contents(ol_str, "li")

                for li in li_contents:
                    if len(li) <= 9 or '<div class="citation-whole">' in li:
                        continue

                    li = li[4:-5]
                    li = remove_tags(li, omissions=["ol", "li", "dd"])
                    
                    sublist = None
                    sub_ol_start = li.find("<ol>")
                    if sub_ol_start >= 0:
                        sub_ol_end = li.rfind("</ol>")
                        if sub_ol_end >= 0:
                            parent_def = li[:sub_ol_start].strip()
                            sublist = li[sub_ol_start + 4:sub_ol_end].strip()
                            print(f"\tli parent: {parent_def}")
                            print(f"\t\tsublist: {sublist}")

                    if sublist is None:
                        print(f"\tli: {li}")
                    
                
                '''for c in contents:
                    if '<div class="citation-whole">' not in c:
                        c = remove_tags(c, omissions=["ol", "li"])
                        print(c)
                        """
                        if len(c) > 9:
                            c = c[4:-5]

                            ol_start = c.find("<ol>")
                            if ol_start >= 0:
                                sub_defs = extract_tag_contents(c, "li")
                                for sub in sub_defs:
                                    print(f"\t\tsubdef: {sub}")
                                c = c[:ol_start]

                            print(f"c:\t{c[4:-5]}")
                        """
                        """sub_ol = ol.find_next("ol")
                        if sub_ol is not None:
                            for s in sub_ol:
                                print(f"\t\ts: {s}")
                        else:
                            print("\tc: " + c)"""
                '''

    #print(e_keys)