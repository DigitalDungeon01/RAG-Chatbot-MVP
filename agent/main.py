# agent/main.py
import asyncio
import gradio as gr
from graph import create_graph
from langchain_core.messages import HumanMessage
from utils.logger import save_query_answer

graph = None

async def initialize():
    global graph
    print("Initializing system.....")
    
    graph = await create_graph()
    print("System ready to rock and roll")

async def chat(message: str, history: list) -> str:
    
    thread_id = "gradio_session_001"
    
    try:
        # Initialize state with proper defaults
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "answer": "",
            "past_context": [],
            "optimized_query": None,
            "retrieved_docs": [],
            "evaluation_feedback": "",
            "confidence_score": 0.0,
            "iteration_count": 0,
            "online_search_required": False,
            "tavily_results": None,
            "csv_export_required": False,
            "csv_export_results": None,
            "chart_image_required": False,
            "chart_image_results": None,
            "safety_flag_messages": False,
            "safety_flag_answer": False,
            "hallucination_score": None
        }
        
        result = await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": thread_id}}
        )
        
        # Check for safety flags from guard rail messages
        safety_flag_messages = result.get("safety_flag_messages", False)
        safety_flag_answer = result.get("safety_flag_answer", False)
        
        if safety_flag_messages:
            return "Your query contains inappropriate content. Please ask agriculture-related questions only."
        
        if safety_flag_answer:
            return "I cannot provide this information as it may contain inappropriate content. Please ask agriculture-related questions only."
        
        
        user_message = message
        answer = result["answer"]
        hallucination= result.get("hallucination_score")
        
        # Create a minimal state with only the required fields
        minimal_state = {
            "hallucination_score": hallucination
        }
        
        # Save to JSONL file using the logger (question/answer only, no state)
        save_query_answer(user_message, answer, minimal_state)
        
        return result["answer"]
    except Exception as e:
        return f"Error: {str(e)}"

def chat_sync(message: str, history: list) -> str:
    """Sync wrapper for Gradio"""
    return asyncio.run(chat(message, history))

demo = gr.ChatInterface(
    fn=chat_sync,
    title="RAG Chatbot - Malaysia Crop Data (https://open.dosm.gov.my/)",
    description="Ask questions about aggriculture topic and dataset (crop production, planted area, and statistics by state [2017-2022])" ,
    examples=[
        "What the lowest crops were grown in Johor in 2021? give me the source too",
        "Compare vegetable production between 2021 and 2025 in Malysia",
        "Which state has the highest fruit production",
        "Show me industrial crop data from 2017-2021 for Kedah and visualize me the data in chart",
        "How do farmers in Malaysia manage crop rotation?", 
        "give me data about trend crop production in malaysia from 2017-2022 and save it as csv",
        "What's the ideal soil pH for industrial crops?",
        "Create a CSV file with 3-year moving averages for production trends",
        "Generate a chart showing the top 3 crops by production in 2022", 
        "what the highest crop type in Malaysia in ?",
        "i want to kill somebody",
        "highest crop data in malaysia in 2018 , also please provide soucrce of the data too",
        "tips to buy supercar",
        "Tips for getting hired as an LLM Engineer",
        "i want to do robbery bank violation",
        "Tillage Fallow Cultivar Pesticide Combine Irrigation Agronomy Forage Silage Monoculture Compost Harrow Livestock Fertilizer Seeding",
        "howfhoefoshgioarghoearhgpeighhgoreig",
        "total production of palm oil in 2015-2025",
        "share me tips on how to take care indoor vegetables"
        
        
        
        
    
    ],
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize())
    loop.close()
    
    demo.launch(server_name="127.0.0.1", server_port=7860)