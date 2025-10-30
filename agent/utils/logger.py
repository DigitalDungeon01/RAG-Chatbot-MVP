import json
import os
from datetime import datetime

# Overwrite the log file at module load (session start)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
eval_dir = os.path.join(project_root, "eval")
os.makedirs(eval_dir, exist_ok=True)

file_path = os.path.join(eval_dir, "query_answer_result.jsonl")


with open(file_path, "w", encoding="utf-8") as f:
    pass

def save_query_answer(user_message, answer, state=None):
    # Create the data structure
    data = {
        "timestamp": datetime.now().isoformat(),
        "user_message": user_message,
        "answer": answer
    }
    
    # Add hallucination score as a top-level field if available
    if state and "hallucination_score" in state:
        data["hallucination_score"] = state["hallucination_score"]
        # Remove hallucination_score from state to avoid duplication
        state_copy = state.copy()
        del state_copy["hallucination_score"]
        data["state"] = state_copy
    elif state:
        data["state"] = state
    

    json_line = json.dumps(data, ensure_ascii=False, indent=2)
    
    # Always append during the session
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json_line + "\n")
