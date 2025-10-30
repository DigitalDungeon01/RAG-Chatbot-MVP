import torch
from langchain_huggingface import HuggingFaceEmbeddings
from pymilvus import MilvusClient
from config import settings

device = "cuda" if torch.cuda.is_available() else "cpu"
embeddings_model = HuggingFaceEmbeddings(
    model_name='all-MiniLM-L6-v2', 
    model_kwargs={'device': device}
)
client = MilvusClient(uri=settings.ZILLIZ_URL, token=settings.ZILLIZ_TOKEN)
collection_name = settings.COLLECTION_NAME


def semantic_search_milvus(query, k):
    """Perform semantic search on Milvus"""
    
    query_vector = embeddings_model.embed_query(query)
    
    results = client.search(
        collection_name=collection_name,
        data=[query_vector],
        limit=k,
        output_fields=[
            "text", 
            
            #"state", "date", "crop_type", "planted_area", "production",
            "source", "dataset_name", "source_url", "data_year"
            # "chunk_id", "created_at"
        ]
    )  
    
    # Return in json format
    json_results = []
    for hits in results:
        for hit in hits:
            json_results.append({
                "text": hit['entity']['text'],
                # "state": hit['entity']['state'],
                # "date": hit['entity']['date'],
                # "crop_type": hit['entity']['crop_type'],
                # "planted_area": hit['entity']['planted_area'],
                # "production": hit['entity']['production'],
                # "source": hit['entity']['source'],
                "dataset_name": hit['entity']['dataset_name'],
                "source_url": hit['entity']['source_url'],
                "data_year": hit['entity']['data_year'],
                # "chunk_id": hit['entity']['chunk_id'],
                # "created_at": hit['entity']['created_at'],
                "score": hit['distance']
            })
    
    return json_results

