# RAG Showdown Analysis Report

Session ID: rag_showdown_20250309_193300  
Document length: 9265 characters  
Processing time: 52.90 seconds  

## Document Analysis

### Document Metrics

- Word count: 1504
- Sentence count: 77
- Paragraph count: 8
- Estimated tokens: 2316

### Document Boundaries

Boundary detection confidence: 9

Detected 2 potential document boundaries:

- Boundary 1: Unknown at position 779
- Boundary 2: Unknown at position 1656
## Chunking Strategy Comparison

### Strategy Ranking

- **Boundary-Aware**: 0.552
- **Semantic**: 0.457
- **Traditional Fixed-Size**: 0.008

### Metrics Comparison

| Strategy | Chunks | Avg Size | Boundary Score | Sentence Score |
|----------|--------|----------|----------------|---------------|
| Traditional Fixed-Size | 213 | 149.1 | 0.00 | 0.03 |
| Boundary-Aware | 11 | 819.6 | 0.78 | 0.03 |
| Semantic | 11 | 819.4 | 0.64 | 0.04 |

## Retrieval Method Comparison

### Retrieval with fixed_size chunking

Fastest method: **context**
Most unique results: **vector**

#### Retrieval Speed

- vector: 0.511s
- entity: 1.978s
- context: 0.001s
- hybrid: 0.011s

### Retrieval with boundary_aware chunking

Fastest method: **context**
Most unique results: **vector**

#### Retrieval Speed

- vector: 0.242s
- entity: 2.066s
- context: 0.001s
- hybrid: 0.009s

## Synthesis Method Comparison

