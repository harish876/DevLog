import google.generativeai as genai
import os

# # Learn more about calling the LLM: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
# def call_llm(prompt):    
#     client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))
#     r = client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     return r.choices[0].message.content
    
def call_llm(prompt):
    api_key = os.environ.get("GOOGLE_API_KEY", "your-api-key")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
