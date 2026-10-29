from backend.app.services.document_service import DocumentService

def test_document_chunking_and_similarity():
    service = DocumentService()
    text = "The quick brown fox jumps over the lazy dog. Artificial intelligence workflows combine machine learning with retrieval augmented generation."
    
    chunks = service.chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) >= 2

    # Bag-of-words vector & cosine similarity
    vec1 = service.compute_bow_vector("artificial intelligence machine learning")
    vec2 = service.compute_bow_vector("artificial intelligence deep learning models")
    vec3 = service.compute_bow_vector("baking sourdough bread at home")

    score_similar = service.cosine_similarity(vec1, vec2)
    score_unrelated = service.cosine_similarity(vec1, vec3)

    assert score_similar > 0.4
    assert score_unrelated < 0.1
