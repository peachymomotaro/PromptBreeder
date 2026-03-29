from concurrent.futures import ThreadPoolExecutor


def chat_text(model, prompt, **kwargs):
    response = model.chat(message=prompt, **kwargs)
    return response.text


def batch_chat_text(model, prompts, max_workers=None, **kwargs):
    def run_chat(prompt):
        return chat_text(model, prompt, **kwargs)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(run_chat, prompts))
