import sys

try:
    import pysqlite3
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass  # fallback if pysqlite3 not available

import pandas as pd
import chromadb
import uuid


class Portfolio:
    def __init__(self, file_path="resource/portfolio_projects.csv"):
        self.file_path = file_path
        self.data = pd.read_csv(file_path)
        self.chroma_client = chromadb.PersistentClient('vectorstore')
        self.collection = self.chroma_client.get_or_create_collection(name="portfolio")

    def load_portfolio(self):
        if not self.collection.count():
            for _, row in self.data.iterrows():
                    # Split comma-separated skills into a list
                    docs = row["Skills"].split(", ")

                    # Add to Chroma
                    self.collection.add(
                        documents=docs,  # list of skills per project
                        metadatas=[{
                            "project_name": row["Project_name"], 
                            "url": row["URL"], 
                            "description": row["Description"]
                        } for _ in docs], # one metadata dict per skill
                        
                        ids=[str(uuid.uuid4()) for _ in docs]  # unique ID per skill
                    )


    def query_links(self, skills):
        return self.collection.query(query_texts= skills , n_results=3).get('metadatas', [])