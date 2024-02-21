import streamlit as st
import chromadb
import llm
import time
from PIL import Image
import transformers
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction, HuggingFaceEmbeddingFunction

# Streamlit config
st.set_page_config(layout="wide")
st.title("Image search engine")

# Enter search term or provide image
option = st.selectbox('How do you want to search?', ('Search Term', 'Image'))
if option == "Search Term":
    uploaded_file = None
    search_term = st.text_input("Enter search term")
else:
    search_term = None
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, width=200)

st.markdown('<hr style="border:1px #00008B; border-style: solid; margin:0;">', 
    unsafe_allow_html=True)


# # Load the Hugging Face model
# model_name = "WhereIsAI/UAE-Large-V1"
# tokenizer = transformers.AutoTokenizer.from_pretrained(model_name)
# model = transformers.AutoModel.from_pretrained(model_name)

# Create a HuggingFaceEmbeddingFunction
# embedding_function = HuggingFaceEmbeddingFunction(
#     tokenizer=tokenizer,
#     model=model,
#     layer_index=-1  # Use the output of the last layer for embeddings
# )

embedding_function = OpenCLIPEmbeddingFunction()

model = llm.get_embedding_model("clip")
chroma_client = chromadb.PersistentClient(path="images.chromadb")
collection = chroma_client.get_collection(name="images", embedding_function=embedding_function)

with st.empty():
    if option and (uploaded_file or search_term):
        start = time.time()
        with st.spinner('Searching'):
            if option == 'Search Term':
                query_embeddings = model.embed(search_term)
            else:
                query_embeddings = model.embed(uploaded_file.getvalue())
            result = collection.query(
                query_embeddings=[query_embeddings],
                n_results=3
            )
        end = time.time()
        print(result)
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]
        with st.container():
            st.write(f"**Results** ({end-start:.2f} seconds)")

            # Calculate number of columns and rows
            num_images = len(result["ids"][0])
            columns_per_row = 3  # Replace with your desired number of columns per row
            num_rows = (num_images + columns_per_row - 1) // columns_per_row

            # Define margin and padding for consistent spacing
            image_spacing = 10  # Adjust spacing as needed
            image_width = 350  # Adjust image width as needed

            for row in range(num_rows):
                # Create columns for this row
                columns = st.columns(columns_per_row)

                # Iterate through images for this row
                for col in range(columns_per_row):
                    index = row * columns_per_row + col  # Calculate index based on row and col
                    if index >= num_images:  # Break if no more images
                        break

                    # Add margin and padding around image
                    with columns[col]:
                        st.markdown(f"<div style='margin: {image_spacing}px;'>", unsafe_allow_html=True)
                        st.image(Image.open(metadatas[index]['filePath']), width=image_width)
                        st.markdown("</div>", unsafe_allow_html=True)

                    # Place information below image in the same column
                    with columns[col]:
                        st.empty()  # Create space for image
                        st.markdown(f"""**Location**: {metadatas[index]['filePath']}  
                                    **Distance**: {distances[index]}""")

    else:
        st.write("No results to show. Enter a search term above.")