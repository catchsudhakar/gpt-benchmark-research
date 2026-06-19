from pathlib import Path
import pandas as pd
import re
import sys

# Add root folder to Python search as utils folder is outside of this directory:
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from utils.api_client import GPTClient


# 1. Load  parquet file
script_dir = Path(__file__).resolve().parent
parquet_path = script_dir / 'AIME-training-dataset.parquet'

aime_data = pd.read_parquet(parquet_path)

# 2. Initialize GPT client
client = GPTClient(model="gpt-4.1-mini", temperature=0.0)

# 3. Run through questions and evaluate
def extract_answer(model_output: str) -> str:
    # Extract final answer
    match = re.search(r'\\boxed{([^}]+)}', model_output, re.DOTALL)
    return match.group(1).strip() if match else ""

def score(model_answer: str, ground_truth: str) -> bool:
    extracted = extract_answer(model_answer)
    print (f"Extracted: {extracted}, Ground Truth: {ground_truth}")
    return extracted == str(ground_truth)



# 4. Compare model answers to ground truth and save results
results = []

#for i in range(len(aime_data)):
for i in range(2):

    question = aime_data["problem"].iloc[i]
    ground_truth = aime_data["answer"].iloc[i]
    
    response = client.complete([{"role": "user", "content": question}])
    #print(response)
    correct = score(response, ground_truth)
    
    results.append({
        "id": i,
        "question": question[:50],
        "ground_truth": ground_truth,
        "model_answer_extracted": extract_answer(response),
        "correct": correct
    })

# 5. Save the results
print ("Done Processing")
pd.DataFrame(results).to_csv("aime_test.csv", index=False)
print(f"Correct: {sum(r['correct'] for r in results)}/{len(results)}")