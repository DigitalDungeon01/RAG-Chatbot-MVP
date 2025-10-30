from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from state import State
from schema import (EvaluationSchema, ChartConfig, GuardRailSchemaMessages, 
                    GuardRailSchemaAnswer, AnswerGenerationSchema, HallucinationResult, TavilySearchSchema)
from llm import llm
from retriever import semantic_search_milvus
from prompts import (filter_prompt, answer_prompt, evaluation_prompt, tavily_search_prompt, csv_generator_prompt, 
                    chart_generator_prompt,guard_rail_prompt_messages, guard_rail_prompt_answer, hallucination_prompt)
from mcp_tools.mcp_client import get_tools # get_csv_gen_tools
import os
import json

        

async def guard_rail_messages(state: State) -> dict:
   
    print("\n\n----------------- QUERY RECEIVED ----------------")
    print(f"user message: {state['messages'][-1].content}")
    print("-----------------------------------")
    print("\n==== Guard Rail Messages Triggered ====\n")
    user_message = state["messages"][-1].content
    
    system_prompt, user_prompt = guard_rail_prompt_messages(user_message)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    
    llm_model = llm.with_structured_output(GuardRailSchemaMessages)
    
    try:
        result = await llm_model.ainvoke(messages)
    except Exception as e:
        print(f"Guard Rail Messages Node Error ! \nError in guard rail messages: {e}")
        
        return {
            "safety_flag_messages": True # JUST END
        }
    
    print(result)
    
    return {
        "safety_flag_messages": result.safety_flag_messages
    }
    
    
async def semantic_optimizer_filter(state: State) -> dict:
    print("\n==== Semantic Optimizer Triggered ====\n")
    
    user_message = state["messages"][-1].content
    system_prompt, user_prompt = filter_prompt(user_message)
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    
    optimized_query = "None"
    
    try:
        response = await llm.ainvoke(messages)  
        optimized_query = response.content.strip()
            
    except Exception as e:
        print(f"Semantic Optimizer Filter Node Error ! \nError parsing user message: {e}")
    
    print("\nsemantic optimizer filter response: ", optimized_query)
    
    return {
        "optimized_query": optimized_query,
    }
    

async def semantic_search(state: State) -> dict:
    print("\n==== Semantic Search Triggered ====\n")
    try:
        optimized_query = state.get("optimized_query")
        k = 13

        if optimized_query is None:
            return {
                "retrieved_docs": []
            }

        # semantic search()
        retrieved_docs = semantic_search_milvus(optimized_query, k)
        
        print(f"Retrieved Docs Success: {bool(retrieved_docs)}")
        for doc in retrieved_docs:
            print(f"Text: {doc['text']}")
            print(f"Similarity Score: {doc['score']}")
            print()
    
        return {
            "retrieved_docs": retrieved_docs
        }
    
    except Exception as e:
        # raise ValueError(f"Error in semantic_search: {e}")
        print(f"Semantic Search Node Error ! \nError in semantic_search: {e}")
        return {
            "retrieved_docs": None,
        }
    

async def answer_generator(state: State) -> dict:
    print("\n==== Answer generator triggered ====\n")
    
    # Extract current state
    user_message = state["messages"][-1].content
    retrieved_docs = state["retrieved_docs"]
    feedback = state["evaluation_feedback"]
    search_results = state["tavily_results"]
    csv_output_results = state["csv_export_results"]
    chart_output_results = state["chart_image_results"]
    
     # FIXED: Build context from stored history snapshots
    past_context_data = state.get("history_snapshots", [])[-3:]  # Last 3 turns
    past_context = json.dumps(past_context_data, indent=2) if past_context_data else None
    
    # print(f"+++Received past context by answer generator LEV 1+++ \n {past_context}")
    
    # Generate answer
    system_prompt, user_prompt = answer_prompt(
        user_message, retrieved_docs, search_results, feedback, 
        past_context, csv_output_results, chart_output_results
    )
    
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    llm_model = llm.with_structured_output(AnswerGenerationSchema)
    
    try:
        result = await llm_model.ainvoke(messages)
    except Exception as e:
        print(f"Answer Generator Node Error!\nError: {e}")
        return {"answer": "Error generating answer"}
    
    # Debug logging
    print(f"\nPast context: {bool(past_context)}")
    print(f"Search results: {bool(search_results)}")
    print(f"CSV results: {bool(csv_output_results)}")
    print(f"Chart results: {bool(chart_output_results)}")
    print(f"Flags - Search: {result.online_search_required}, CSV: {result.csv_export_required}, Chart: {result.chart_image_required}")
    print(f"User: {user_message}")
    print(f"Answer: {result.answer}")
    
    # print(f"+++Received serach result by answer generator LEV 2+++ \n {search_results}")
    
    
    # Store current snapshot for next iteration
    current_snapshot = {
        "user_message": user_message,
        "answer": result.answer,
        "search_results_present": bool(search_results),
        "csv_results_present": bool(csv_output_results),
        "chart_results_present": bool(chart_output_results)
    }
    
    # Prevent flag loops - only set True if results don't exist yet
    return {
        "answer": result.answer,
        "csv_export_required": result.csv_export_required and not csv_output_results,
        "chart_image_required": result.chart_image_required and not chart_output_results,
        "online_search_required": result.online_search_required and not search_results,
        "iteration_count": state["iteration_count"] + 1,
        "history_snapshots": state.get("history_snapshots", []) + [current_snapshot]  # NEW
    }


async def evaluation(state: State) -> dict:
    print("\n==== Evaluation triggered ====\n")
    user_message = state["messages"][-1].content
    answer = state["answer"]
    retrieved_docs = state["retrieved_docs"]


    system_prompt, user_prompt = evaluation_prompt(user_message, answer, retrieved_docs)
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    llm_model = llm.with_structured_output(EvaluationSchema)
    
    try:
        result = await llm_model.ainvoke(messages)
        
        print(f"\nfeedback: {result.feedback}")
        print(f"confidence score: {result.confidence_score}")
        print(f"iteration count: {state['iteration_count']}")
        
    except Exception as e:
        # raise ValueError(f"Error evaluating answer: {e}")
        raise ValueError(f"Evaluation Node Error ! \nError evaluating answer: {e}")

    return {
        "confidence_score": result.confidence_score,
        "feedback": result.feedback,
    }
    


async def tavily_search_node(state: State) -> dict:
    print("\n==== tavily generator triggered ====\n")
    
    user_message = state["messages"][-1].content
    
   # get past context
    past_context_data = []
    start_idx = max(0, len(state["messages"]) - 2)  # last 3 messages

    for i in range(start_idx, len(state["messages"]) - 1):  # exclude the last one
        msg_obj = state["messages"][i]
        msg_content = msg_obj.content if hasattr(msg_obj, "content") else str(msg_obj)

        snapshot = {
            "history": {
                "messages": [msg_content],
                "answer": [state["answer"]] if state["answer"] else [None],
            }
        }
        past_context_data.append(snapshot)

    # convert to JSON string
    past_context = json.dumps(past_context_data, indent=2)
    
    print(f"\n past context for tavily search received: {bool(past_context)} \n")
    
    try:
        tools = await get_tools()
        tavily_tool = next((t for t in tools if "search" in t.name.lower()), None)  # loop thru all tools and find the search tool

        if not tavily_tool:
            print("Warning: Tavily tool not found")
            return {
                "tavily_results": None,
                "online_search_required": False  # Reset flag to stop looping
            }

        system_prompt, user_prompt = tavily_search_prompt(user_message, past_context)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        # bind tools to LLM
        llm_with_tools = llm.bind_tools([tavily_tool])
        response = await llm_with_tools.ainvoke(messages)

        tool_call = response.tool_calls[0]
        result = await tavily_tool.ainvoke(tool_call["args"])  # execute tool call

        print(f"tavily search results: {bool(result)}")

        return {
            "tavily_results": result, # Reset flag after use
            "online_search_required": False,
        }

    except Exception as e:
        print(f"Error in tavily search node: {e}")
        return {
            "tavily_results": None,
        }


async def csv_generator(state: State) -> dict:
    print("\n==== CSV generator triggered ====\n")
    
    user_message = state["messages"][-1].content
    answer = state["answer"]
    data_context = state["retrieved_docs"]
    search_results = state["tavily_results"]
    
     # get past context
    past_context_data = []
    start_idx = max(0, len(state["messages"]) - 3)  # last 3 messages

    for i in range(start_idx, len(state["messages"]) - 1):  # exclude the last one
        msg_obj = state["messages"][i]
        msg_content = msg_obj.content if hasattr(msg_obj, "content") else str(msg_obj)

        snapshot = {
            "History": {
                "messages": [msg_content],
                "answer": [state["answer"]] if state["answer"] else [None],
                "data_context": [state["retrieved_docs"]] if state["retrieved_docs"] else [None],
                "search_results": [state["tavily_results"]] if state["tavily_results"] else [None],
            }
        }
        past_context_data.append(snapshot)

    # convert to JSON string
    past_context = json.dumps(past_context_data, indent=2)

    
    print(f"\n past context for csv generation received: {bool(past_context)} \n")
    try:
        tools = await get_tools()
        csv_tool = next((t for t in tools if "csv" in t.name.lower()), None)
        
        if not csv_tool:
            print("Warning: CSV tool not found")
            return {
                "csv_export_required": False,  # Reset flag to stop looping
                "csv_export_results": "Error: CSV generation tool not available."
            }
        
        system_prompt, user_prompt = csv_generator_prompt(user_message, data_context, search_results, past_context)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        
        # bind tools to LLM
        llm_with_tools = llm.bind_tools([csv_tool])
        response = await llm_with_tools.ainvoke(messages)
        
        tool_call = response.tool_calls[0]
        filepath = await csv_tool.ainvoke(tool_call["args"])  # execute tool call
        
        
        filename = os.path.basename(filepath) # file path
        
        print(f"CSV file generated: {filename}")
        print(f"CSV generated file path: {filepath}")
        
        return {
            "csv_export_required": False,
            "csv_export_results": filename
        }
        
    except Exception as e:
        error_message = f"{answer}\n\nError generating CSV: {e}"
        print(f"CSV generation error: {e}")
        return {
            "csv_export_required": False,
            "csv_export_results": "Error generating CSV"
        }



async def chart_generator(state: State) -> dict:
    print("\n==== Chart generator triggered ====\n")

    try:
        user_message = state["messages"][-1].content
        past_context = None
        retrieved_docs = state.get("retrieved_docs", None)
        search_results = state.get("tavily_results", None)

        tools = await get_tools()
        chart_tool = next((t for t in tools if "chart" in t.name.lower()), None)

        if not chart_tool:
            print("Warning: Chart tool not found")
            return {
                "chart_image_required": False,  # Reset flag
                "chart_image_results": "Error: Chart tool not available."
            }
            
        # get past context
        past_context_data = []
        start_idx = max(0, len(state["messages"]) - 3) # last 3
        for i in range(start_idx, len(state["messages"]) - 1): # except last one
            msg_obj = state["messages"][i]
            msg_content = msg_obj.content if hasattr(msg_obj, "content") else str(msg_obj)
            
            snapshot = {
                "History": {
                "messages": [msg_content],
                "answer": [state["answer"]] if state["answer"] else [None],
                "data_context": [state["retrieved_docs"]] if state["retrieved_docs"] else [None],
                "search_results": [state["tavily_results"]] if state["tavily_results"] else [None],
                }}
            past_context_data.append(snapshot)
        
        past_context = json.dumps(past_context_data, indent=2)

        system_prompt, user_prompt = chart_generator_prompt(user_message, past_context, retrieved_docs, search_results)

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        # LLM creates ChartConfig
        llm_with_schema = llm.with_structured_output(ChartConfig)
        config = await llm_with_schema.ainvoke(messages)

        config_dict = config.model_dump()
        chart_url = await chart_tool.ainvoke(config_dict)

        print(f"Chart generated successfully: {chart_url}")

        return {
            "chart_image_required": False,  # Reset flag after use
            "chart_image_results": chart_url
        }

    except Exception as e:
        error_msg = f"Chart generation error: {e}"
        print(error_msg)
        return {
            "chart_image_required": False,  # Reset flag after use
            "chart_image_results": "Error generating chart"
        }



async def guard_rail_answer(state: State) -> dict:
    print("\n==== Guard Rail Final Check Triggered ====\n")

    answer = state["answer"]
    safety_flag_answer = False  # Default to safe
    
    try:
        system_prompt, user_prompt = guard_rail_prompt_answer(answer)
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        response = await llm.ainvoke(messages)
        response_text = response.content.strip().upper()
        
        # Check if response contains TRUE (violating)
        if "TRUE" in response_text:
            safety_flag_answer = True
        
        print(f"\nGuard rail answer response: {safety_flag_answer}\n")
        print("\n----------------- RESULT ----------------")
        print(f"user message: {state['messages'][-1].content}")
        print(f"answer: {answer}")
        print("-----------------------------------")
        print("\n\n# [==End Of Process==] #\n\n")

    except Exception as e:
        print(f"Error in guard rail answer: {e}")
        # safety_flag_answer stays False (safe default)
    
    return {
        "safety_flag_answer": safety_flag_answer
    }

    
    
async def hallucination_calculator(state: dict) -> dict:
    print("\n==== Hallucination Calculator Triggered ====\n")

    try:
        answer = state.get("answer", "")
        retrieved_docs = state.get("retrieved_docs")
        search_results = state.get("search_results")

        system_prompt, user_prompt = hallucination_prompt(answer, retrieved_docs, search_results)

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

        llm_with_schema = llm.with_structured_output(HallucinationResult)
        result = await llm_with_schema.ainvoke(messages)

        print(f"Hallucination score: {result.hallucination_score}")

        return {
            "hallucination_score": result.hallucination_score
        }

    except Exception as e:
        print(f"Error in hallucination calculator: {e}")
        return {
            "hallucination_score": 0.0
        }


