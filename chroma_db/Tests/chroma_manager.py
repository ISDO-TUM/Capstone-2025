import chromadb

# Connect to the Chroma server
client = chromadb.HttpClient(host="localhost", port=8000)  # Adjust host/port if needed

# NOTE: The following block is for local testing only. Uncomment to run local ChromaDB management tests.
# # List collections and item counts
# collections = client.list_collections()
# print("Collections and item counts:")
#
# for coll in collections:
#     collection = client.get_collection(coll.name)
#     items = collection.get()
#     count = len(items["ids"])
#     print(f"- {coll.name}: {count} items")
#
# # Prompt to delete all collections
# confirm = input("\nType 'YES' to delete all collections: ")
# if confirm == "YES":
#     for coll in collections:
#         client.delete_collection(coll.name)
#         print(f"Deleted collection: {coll.name}")
# else:
#     print("Aborted deletion.")
