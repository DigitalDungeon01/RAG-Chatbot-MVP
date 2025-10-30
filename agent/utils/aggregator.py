import pandas as pd

def aggregate_data(docs: list) -> dict:
    """Aggregate retrieved documents"""
    
    df = pd.DataFrame(docs)
    
    # Extract metadata from first document
    first_doc = docs[0] if docs else {}
    
    return {
        "total_records": len(docs),
        "date_range": f"{df['date'].min()} to {df['date'].max()}",
        "metadata": {
            "source": first_doc["source"],
            "dataset_name": first_doc["dataset_name"],
            "source_url": first_doc["source_url"],
            "data_year": first_doc["data_year"]
        },
        "summary": {
            "total_production": float(df['production'].sum()),
            "total_planted_area": float(df['planted_area'].sum()),
            "avg_production": float(df['production'].mean()),
            "avg_planted_area": float(df['planted_area'].mean())
        },
        "by_year": df.groupby('date')['production'].sum().to_dict(),
        "by_state": df.groupby('state')['production'].sum().to_dict(),
        "by_crop_type": df.groupby('crop_type')['production'].sum().to_dict()
    }