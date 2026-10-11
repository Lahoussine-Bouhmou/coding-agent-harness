import os

from openai import OpenAI


def main():
    client = OpenAI(
        api_key=os.environ["API_KEY"],
        base_url=os.environ["BASE_URL"],
    )
    prompt = input("Enter your prompt> ")
    response = client.chat.completions.create(
        model=os.environ.get("MODEL", "openrouter/free"),
        messages=[
            {"role": "system", "content": "You are a coding agent. Write code to solve the user's request."},
            {"role": "user", "content": prompt},
        ],
    )
    print(f"\nAgent: {response.choices[0].message.content}\n")
    if response.usage is not None:
        usage = response.usage
        print({
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "reasoning_tokens": getattr(usage.completion_tokens_details, "reasoning_tokens", None),
            "cached_tokens": getattr(usage.prompt_tokens_details, "cached_tokens", None),
        })


if __name__ == "__main__":
    main()
