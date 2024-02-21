import llm
import glob
import base64
import hashlib
import chromadb
from rich import console

# model = llm.get_embedding_model("all-mpnet-base-v2")
model = llm.get_embedding_model("clip")

images = glob.glob("images/*.jpg")

embeddings = []
for image in images:
  with open(image, "rb") as image_file:
    embedding = model.embed(image_file.read())
    embeddings.append({
      "embedding": embedding,
      "filePath": image,
      "id": base64.b64encode(hashlib.sha256(image.encode()).digest()).decode()
    })


chroma_client = chromadb.PersistentClient(path="images.chromadb")
collection = chroma_client.create_collection(name="images")
collection.add(
    embeddings=[e["embedding"] for e in embeddings],
    metadatas=[{k: e[k] for k in ["filePath"]} for e in embeddings],
    ids=[e["id"] for e in embeddings],
)
