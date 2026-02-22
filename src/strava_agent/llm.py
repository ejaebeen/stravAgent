from langchain_ollama import ChatOllama

def get_llm(model: str, temperature: float = 0):
    """
    Create and return a ChatOllama client.
    
    Args:
        model: The model name to use (e.g., 'qwen3:8b', 'llama3.1').
        temperature: The temperature for generation (0.0 to 1.0).
    """
    return ChatOllama(
        model=model,
        temperature=temperature
    )