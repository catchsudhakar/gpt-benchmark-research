from pathlib import Path
import pandas as pd
import re
import sys
import time

# Add root folder to Python search as utils folder is outside of this directory:
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from utils.api_client import GPTClient

# Get GPT Cost reference file
cost_ref = pd.read_csv(project_root/'utils/GPT-model-costs-june-2026.csv')
cost_ref.columns = cost_ref.columns.str.strip()
cost_ref['Model'] = cost_ref['Model'].str.strip().str.lower()

def get_model_costs(input_name):
    # Standardize user input to match the CSV format (lowercase, replace spaces with dashes)
    target_model = GPTMODEL_NAME.lower().replace(" ", "-")
    
    # Filter the DataFrame for the matching model row
    result = cost_ref[cost_ref['Model'] == target_model]
    
    if not result.empty:
        # Fetch costs from the row
        input_price = result['Input Cost'].values[0]
        output_price = result['Output Cost'].values[0]
    else:
        print(f"❌ Model '{target_model}' not found in the CSV.")
        input_price = 0.15
        output_price = 0.6
    return float(input_price), float(output_price)  

# Initialize GPT client
GPTMODEL_NAME = "gpt-4.1-mini"
client = GPTClient(model=GPTMODEL_NAME, temperature=0.0)
input_price, output_price = get_model_costs(GPTMODEL_NAME)

#  Load  parquet file
script_dir = Path(__file__).resolve().parent
parquet_path = script_dir / 'AIME-training-dataset.parquet'

aime_data = pd.read_parquet(parquet_path)



#  Run through questions and evaluate
def extract_answer(model_output: str) -> str:
    # Extract final answer
    match = re.search(r'\\boxed{([^}]+)}', model_output, re.DOTALL)
    return match.group(1).strip() if match else ""

def score(model_answer: str, ground_truth: str) -> bool:
    extracted = extract_answer(model_answer)
    print (f"Extracted: {extracted}, Ground Truth: {ground_truth}")
    return extracted == str(ground_truth)



#  Compare model answers to ground truth and save results
results = []

#for i in range(len(aime_data)):
for i in range(2):

    question = aime_data["problem"].iloc[i]
    ground_truth = aime_data["answer"].iloc[i]
# Measure latency
    start = time.perf_counter() 
    response = client.complete([{"role": "user", "content": question}])
    end = time.perf_counter()
    
    correct = score(response["text"], ground_truth)

# Measure cost

    input_tokens = response["usage"].prompt_tokens
    output_tokens = response["usage"].completion_tokens

    cost = (input_tokens / 1_000_000 * input_price) + \
       (output_tokens / 1_000_000 * output_price)

    results.append({
        "model_used": GPTMODEL_NAME,
        "id": i,
        "question": question[:50],
        "ground_truth": ground_truth,
        "model_answer_extracted": extract_answer(response["text"]),
        "correct": correct,
        "latency in seconds": end - start,
        "cost in USD": cost
    })

# 5. Save the results
print ("Done Processing")
pd.DataFrame(results).to_csv(f"{script_dir}/aime_test_results.csv", index=False)
print(f"Correct: {sum(r['correct'] for r in results)}/{len(results)}")