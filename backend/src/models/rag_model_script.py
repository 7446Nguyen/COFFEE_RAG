# %%
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.constants import (OPENAI_ACCOUNT, PINECONE_ACCOUNT, SYS_PROMPT)
from pinecone import Pinecone, ServerlessSpec
import openai
import time



# %%
# configure client
pc = Pinecone(api_key=PINECONE_ACCOUNT)
index_name = 'coffee-reviews'

# check if index already exists (it shouldn't if this is first time)
if index_name not in pc.list_indexes().names():
    # if does not exist, create index
    pc.create_index(
        index_name,
        dimension=1536,  # dimensionality of text-embedding-ada-002
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region='us-east-1')
    )
# connect to index
index = pc.Index(index_name)
# view index stats
index.describe_index_stats()


# %%
# get api key from platform.openai.com
openai.api_key = OPENAI_ACCOUNT
embed_model = "text-embedding-ada-002"


# %%

def retrieve(query, top_k=3, limit=4000):

    # Get query embedding
    response = openai.Embedding.create(
        input=[query], model="text-embedding-ada-002")
    query_embedding = response['data'][0]['embedding']

    # Query Pinecone for top-k matches
    response = index.query(vector=query_embedding,
                           top_k=top_k, include_metadata=True)

    # Extract contexts
    contexts = [
        f"Name: {match['metadata'].get('name', 'N/A')}\n"
        f"Roaster: {match['metadata'].get('roaster', 'N/A')}\n"
        f"Rating: {match['metadata'].get('rating', 'N/A')}\n"
        f"Flavor: {match['metadata'].get('desc_flavor', 'N/A')}\n"
        f"Overview: {match['metadata'].get('desc_overview', 'N/A')}\n"
        f"Package: {match['metadata'].get('desc_package', 'N/A')}\n"
        f"Opinion: {match['metadata'].get('desc_opinion', 'N/A')}\n"
        for match in response['matches']
    ]

    # Build the final prompt with a dynamic length limit
    prompt = "Answer the question based on the context below.\n\nContext:\n"

    added_length = 0
    for ctx in contexts:
        if added_length + len(ctx) < limit:
            prompt += f"{ctx}\n\n---\n\n"
            added_length += len(ctx)
        else:
            break  # Stop if adding more text exceeds the token limit

    # Append user question
    prompt += f"\nQuestion: {query}\nAnswer:"

    return prompt


def complete(prompt,sys_prompt, model="gpt-4-turbo"):
    """
    Calls OpenAI ChatGPT with a structured prompt.
    """

    res = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    return res['choices'][0]['message']['content'].strip()


# Full RAG Pipeline
def rag_pipeline(user_query):
    prompt = retrieve(user_query)
    response = complete(prompt, SYS_PROMPT)
    return response


#%% Example usage
user_query = "Is a coffee color paint a good idea for my face?"
response = rag_pipeline(user_query)
print(response)

# %%
