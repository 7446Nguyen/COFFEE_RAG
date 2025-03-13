import os
import openai
from pinecone import Pinecone, ServerlessSpec
from backend.src.utils.constants import OPENAI_ACCOUNT, PINECONE_ACCOUNT, SYS_PROMPT

# Initialize Pinecone and OpenAI
class RAGModel:
    def __init__(self, index_name='coffee-reviews'):
        """Initialize RAG model with Pinecone index and OpenAI API key."""
        self.index_name = index_name
        self.pc = Pinecone(api_key=PINECONE_ACCOUNT)
        openai.api_key = OPENAI_ACCOUNT
        self.embed_model = "text-embedding-ada-002"

        # Ensure the index exists
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                index_name,
                dimension=1536,  # Dimensionality for text-embedding-ada-002
                metric='cosine',
                spec=ServerlessSpec(cloud='aws', region='us-east-1')
            )

        # Connect to index
        self.index = self.pc.Index(index_name)

    def retrieve(self, query, top_k=3, limit=4000):
        """Retrieve relevant context from Pinecone using OpenAI embeddings."""
        try:
            # Get query embedding
            response = openai.Embedding.create(input=[query], model=self.embed_model)
            query_embedding = response['data'][0]['embedding']

            # Query Pinecone for top-k matches
            response = self.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

            # Extract context from matched results
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

            # Build the final prompt dynamically within token limit
            prompt = "Answer the question based on the context below.\n\nContext:\n"
            added_length = 0

            for ctx in contexts:
                if added_length + len(ctx) < limit:
                    prompt += f"{ctx}\n\n---\n\n"
                    added_length += len(ctx)
                else:
                    break  # Stop if adding more text exceeds the limit

            prompt += f"\nQuestion: {query}\nAnswer:"
            return prompt

        except Exception as e:
            return f"Error during retrieval: {str(e)}"

    def complete(self, prompt, sys_prompt=SYS_PROMPT, model="gpt-4-turbo"):
        """Generate a response using OpenAI ChatCompletion."""
        try:
            res = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            return res['choices'][0]['message']['content'].strip()

        except Exception as e:
            return f"Error during completion: {str(e)}"

    def rag_pipeline(self, user_query):
        """Full RAG pipeline: retrieve relevant info + generate response."""
        prompt = self.retrieve(user_query)
        if "Error" in prompt:  # Handle retrieval errors
            return prompt
        response = self.complete(prompt)
        return response


# Instantiate RAG model globally (so it's initialized once)
rag_model = RAGModel()
