from groq import Groq

class GROQAnalyst:
  def __init__(self, API_key):
    self.client = Groq(api_key= API_key)

  def get_analysis(self,prompt: str) -> str:
    chat_completion = self.client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
        ],
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content