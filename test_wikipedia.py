from wikipedia_search import wikipedia_search

results = wikipedia_search("What is artificial intelligence?")

print("Results found:", len(results))

for item in results:
    print("\nTitle:", item["title"])
    print("URL:", item["url"])
    print("Content:", item["text"][:300])