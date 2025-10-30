import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # llm
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    # vector store config
    ZILLIZ_URL = os.getenv("ZILLIZ_URL", "")
    ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN", "")
    COLLECTION_NAME = "crop_by_state_data_malaysia"
    
    # MCP_MEMORY_DIR = "./database/user-database"
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
    
    CSV_GEN_OUTPUT_DIR = "./database/user-database"

settings = Settings()

