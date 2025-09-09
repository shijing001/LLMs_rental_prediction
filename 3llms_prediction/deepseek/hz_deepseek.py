import csv
import time
import concurrent.futures
from openai import OpenAI

# 初始化 DeepSeek 客户端
client = OpenAI(api_key="", base_url="https://api.deepseek.com")

# 文件路径
csv_file = r"E:\Jupyter_files\LLM_hz_transformed.csv"
output_file = r"E:\Jupyter_files\output_hz.csv"

batch_size = 5  # 每次批量处理 5 条数据
retry_delay = 5  # 失败后重试等待时间
max_workers = 5  # 最大并发数

data_rows = []  # 存储最终数据

# 读取 CSV 数据
with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames + ["zero_shot_answer", "one_shot_answer", "five_shot_answer", "ten_shot_answer","twenty_shot_answer"]
    rows = list(reader)  # 读取所有数据

# 定义 API 调用函数
def process_row(row):
    text = row["文本"]
    question = row["问题"]
    context = f"Context: {text}\nQuestion: {question}"

    try:
        # 让模型自动生成示例
        example_prompt = f"Given the following context, generate the most relevant examples for reasoning:\nContext: {text}\nQuestion: {question}\nProvide examples in user/assistant format."
        example_response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[{"role": "system", "content": "You are a helpful assistant."},
                      {"role": "user", "content": example_prompt}]
        )
        examples = example_response.choices[0].message.content.split('\n')

        # 处理示例数据，保证格式正确
        structured_examples = []
        for i in range(0, len(examples), 2):
            if i + 1 < len(examples):
                structured_examples.append({"role": "user", "content": examples[i]})
                structured_examples.append({"role": "assistant", "content": examples[i + 1]})

        # 并行请求 Zero-shot、One-shot、Five-shot、Ten-shot
        def query_model(messages):
            for _ in range(3):  # 最多重试 3 次
                try:
                    response = client.chat.completions.create(model="deepseek-reasoner", messages=messages)
                    return response.choices[0].message.content
                except Exception as e:
                    print(f"API Error: {e}, retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
            return "Error: Unable to get response."

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                "zero_shot_answer": executor.submit(query_model, [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": context}]),
                "one_shot_answer": executor.submit(query_model, [{"role": "system", "content": "You are a helpful assistant."}] + structured_examples[:2] + [{"role": "user", "content": context}]),
                "five_shot_answer": executor.submit(query_model, [{"role": "system", "content": "You are a helpful assistant."}] + structured_examples[:10] + [{"role": "user", "content": context}]),
                "ten_shot_answer": executor.submit(query_model, [{"role": "system", "content": "You are a helpful assistant."}] + structured_examples[:20] + [{"role": "user", "content": context}]),
                "twenty_shot_answer": executor.submit(query_model, [{"role": "system", "content": "You are a helpful assistant."}] + structured_examples[:30] + [{"role": "user", "content": context}]),
            }
            # 获取结果
            for key, future in futures.items():
                row[key] = future.result()

        return row

    except Exception as e:
        print(f"Error processing row: {e}")
        return row  # 返回原始数据，避免丢失

# 使用多线程批量处理
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    results = list(executor.map(process_row, rows))

# 保存到 CSV
with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"处理完成，结果已保存到 {output_file}")
