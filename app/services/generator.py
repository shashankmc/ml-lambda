from transformers import pipeline as hf_pipeline
from sentence_transformers import SentenceTransformer
from loguru import logger
from app.config import settings

_summarizer = None
_embedder = None

def get_summarizer():
    """Load and cache the summarization model."""
    global _summarizer
    if _summarizer is None:
        logger.info(f"Loading summarization model: {settings.summarization_model}")
        _summarizer = hf_pipeline(
            "summarization",
            model=settings.summarization_model,
            device=0 if _has_gpu() else -1,  # Use GPU if available
        )
        logger.info("Summarization model loaded")
    return _summarizer

def get_embedder():
    """Load and cache the embedding model."""
    global _embedder
    if _embedder is None:
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedder = SentenceTransformer(settings.embedding_model)
        logger.info("Embedding model loaded")
    return _embedder

def _has_gpu():
    """Check if GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except:
        return False

def summarize_text(text: str, min_length: int = 50, max_length: int = 150) -> str:
    """
    Summarize text using the loaded model.
    
    Args:
        text: Text to summarize
        min_length: Minimum summary length
        max_length: Maximum summary length
    
    Returns:
        Summary text
    """
    summarizer = get_summarizer()
    
    # Split into chunks if text is too long
    max_input_length = 1024  # BART max input
    if len(text) > max_input_length:
        # Simple chunking strategy: split by sentences
        sentences = text.split(". ")
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) > max_input_length:
                chunks.append(current_chunk)
                current_chunk = sentence + ". "
            else:
                current_chunk += sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Summarize each chunk and combine
        summaries = []
        for chunk in chunks:
            if chunk.strip():
                result = summarizer(chunk, min_length=min_length, max_length=max_length, do_sample=False)
                summaries.append(result[0]["summary_text"])
        
        return " ".join(summaries)
    else:
        result = summarizer(text, min_length=min_length, max_length=max_length, do_sample=False)
        return result[0]["summary_text"]

def embed_text(text: str) -> list[float]:
    """
    Generate embedding for text.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector
    """
    embedder = get_embedder()
    return embedder.encode(text).tolist()
