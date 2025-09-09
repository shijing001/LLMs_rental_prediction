import csv
import time
import concurrent.futures
from openai import OpenAI

# OpenAI API 配置
API_key = ""
API_base = "https://api.f2gpt.com/v1"
client = OpenAI(api_key=API_key, base_url=API_base)

# 文件路径
csv_file = "LLM_hz_transformed.csv"  # 输入 CSV 文件
output_file = "output_hz.csv"  # 结果保存路径

batch_size = 5  # 每次批量处理 5 条数据
retry_delay = 5  # 失败后重试等待时间
max_workers = 2  # 降低并发数，避免 API 速率限制

# 读取 CSV 数据
with open(csv_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames + ["zero_shot_answer", "one_shot_answer", "five_shot_answer", "ten_shot_answer","twenty_shot_answer"]
    rows = list(reader)


# 定义 API 调用函数
def query_model(messages):
    """调用 OpenAI API，并处理错误"""
    for attempt in range(3):  # 最多重试 3 次
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=1.0
            )

            if response and response.choices:
                return response.choices[0].message.content.strip()
            else:
                print(f"API Warning: Empty response. Retrying ({attempt + 1}/3)...")
                time.sleep(retry_delay)
        except Exception as e:
            print(f"API Error: {e}, retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    return "Error: Unable to get response after 3 attempts"


# 处理每一行数据
def process_row(row):
    text = row["文本"]
    question = row["问题"]
    context = f"Context: {text}\nQuestion: {question}"

    try:
        # 生成示例数据
        example_prompt = f"Generate the most relevant examples for reasoning:\nContext: {text}\nQuestion: {question}\nProvide examples in user/assistant format."
        example_response = query_model([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": example_prompt}
        ])

        examples = example_response.split('\n')
        structured_examples = []
        for i in range(0, len(examples), 2):
            if i + 1 < len(examples):
                structured_examples.append({"role": "user", "content": examples[i]})
                structured_examples.append({"role": "assistant", "content": examples[i + 1]})

        # 并行请求 Zero-shot、One-shot、Five-shot、Ten-shot
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                "zero_shot_answer": executor.submit(query_model, [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": context}
                ]),
                "one_shot_answer": executor.submit(query_model, [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + structured_examples[:2] + [{"role": "user", "content": context}]),
                "five_shot_answer": executor.submit(query_model, [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + structured_examples[:10] + [{"role": "user", "content": context}]),
                "ten_shot_answer": executor.submit(query_model, [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + structured_examples[:20] + [{"role": "user", "content": context}]),
                "twenty_shot_answer": executor.submit(query_model, [
                    {"role": "system", "content": "You are a helpful assistant."}
                ] + structured_examples[:30] + [{"role": "user", "content": context}])
            }
            for key, future in futures.items():
                row[key] = future.result()

        return row

    except Exception as e:
        print(f"Error processing row: {e}")
        return row


# 使用多线程批量处理
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    results = list(executor.map(process_row, rows))

# 保存到 CSV
with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"处理完成，结果已保存到 {output_file}")
