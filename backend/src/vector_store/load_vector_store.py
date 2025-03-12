#%%
import os
import sys
from typing import List, Union
import time

import openai
import pandas as pd
from tqdm.auto import tqdm
from pinecone import Pinecone, ServerlessSpec

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.constants import (OPENAI_ACCOUNT, PINECONE_ACCOUNT, CLEAN_DATA)

tqdm.pandas()

#%%
def read_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    return df

# Maximum number of texts per API request
BATCH_SIZE = 10  

def get_embedding(texts: Union[str, List[str]], model="text-embedding-ada-002", max_retries=3) -> List[List[float]]:
    """
    Converts a text or list of text strings into embedding vectors.

    Args:
        texts (str or List[str]): Input text(s) to be converted into embeddings.
        model (str): OpenAI embedding model (default: "text-embedding-ada-002").
        max_retries (int): Number of retries in case of API failure.

    Returns:
        List[List[float]]: List of embedding vectors.
    """
    if isinstance(texts, str):
        texts = [texts]  # Convert single string into a list

    embeddings = []
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        retries = 0

        while retries < max_retries:
            try:
                response = openai.Embedding.create(input=batch, model=model, timeout=60)
                batch_embeddings = [item["embedding"] for item in response["data"]]
                embeddings.extend(batch_embeddings)
                break  # Success, exit retry loop

            except openai.error.OpenAIError as e:
                print(f"⚠️ OpenAI API error on batch {i}-{i+len(batch)}: {e}")
                retries += 1
                time.sleep(2 ** retries)  # Exponential backoff (2, 4, 8 sec)

    return embeddings if len(embeddings) > 1 else embeddings[0]  # Return a single embedding if input was a string


def initialize_pinecone(api_key: str, index_name: str) -> Pinecone:
    """
    Initializes Pinecone with the given API key and environment, creates an index, 
    and returns a Pinecone instance.

    Args:
        api_key (str): The API key for authenticating with Pinecone.
        env (str): The environment in which the Pinecone index should be initialized.
        index_name (str): The name of the Pinecone index to create.

    Returns:
        Pinecone: The initialized Pinecone client."
    """

    pc = Pinecone(api_key=api_key)
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # Replace with your model dimensions
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    return pc

def batch_upsert(index, vectors, batch_size):
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(batch)
        print(f"✅ Upserted batch {i} to {i + batch_size}")

#%%

df_coffee = read_csv(CLEAN_DATA)
df_coffee.fillna(0, inplace = True)
# Generate embeddings from `desc_flavor`, `desc_overview`, `desc_opinion`
df_coffee["embedding"] = df_coffee.progress_apply(lambda row: get_embedding(f"{row['desc_flavor']} {row['desc_overview']} {row['desc_opinion']}"), axis=1)


#%%
# Format data for Pinecone
vectors = [
    (
        str(row["index"]),
        row["embedding"],  # Vector embedding
        {  # Metadata (for filtering)
            "name": row['name'],
            "rating": row["rating"],
            "roaster": row["roaster"],
            "region": row["region"], 
            "type_espresso": row["type_espresso"],
            "type_organic": row["type_organic"],
            "type_fair_trade": row["type_fair_trade"],
            "type_decaffeinated": row["type_decaffeinated"],
            "type_pod_capsule": row["type_pod_capsule"],
            "roast": row["roast"],
            "agtron": row["agtron"],
            "aroma": row["aroma"],
            "acid": row["acid"],
            "body": row["body"],
            "flavor": row["flavor"],
            "aftertaste": row["aftertaste"],
            "review_date": row["review_date"],
            "est_price": row["est_price"],
            "desc_flavor": row["desc_flavor"],	
            "desc_overview": row["desc_overview"],	
            "desc_package": row["desc_package"],	
            "desc_opinion": row["desc_opinion"]

        }
    )
    for _, row in df_coffee.iterrows()
]

pc = initialize_pinecone(PINECONE_ACCOUNT, 'coffee-reviews')
index = pc.Index('coffee-reviews')

#%%
batch_upsert(index, vectors, 100)
# %%
