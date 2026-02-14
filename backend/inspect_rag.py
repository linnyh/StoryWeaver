
import chromadb
from app.config import settings
import os

def inspect_chroma():
    # Force absolute path to match backend's location
    persist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_data"))
    print(f"ChromaDB Directory: {persist_dir}")
    
    client = chromadb.PersistentClient(path=persist_dir)
    
    try:
        collection = client.get_collection("scene_summaries")
        print(f"Collection 'scene_summaries' found.")
        print(f"Count: {collection.count()}")
        
        # Get all items
        results = collection.get()
        if not results['ids']:
            print("No documents found in collection.")
            return

        print("\n=== Documents in 'scene_summaries' ===")
        for i in range(len(results['ids'])):
            print(f"\nID: {results['ids'][i]}")
            print(f"Metadata: {results['metadatas'][i]}")
            print(f"Content Preview: {results['documents'][i][:50]}...")
            
    except Exception as e:
        print(f"Error accessing collection: {e}")

if __name__ == "__main__":
    inspect_chroma()
