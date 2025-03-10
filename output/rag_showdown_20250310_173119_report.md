# RAG Showdown Analysis Report

Session ID: rag_showdown_20250310_173119  
Document length: 9265 characters  
Processing time: 34.77 seconds  

## Document Analysis

### Document Metrics

- Word count: 1504
- Sentence count: 77
- Paragraph count: 8
- Estimated tokens: 2316

### Document Boundaries

Boundary detection confidence: N/A

## Chunking Strategy Comparison

### Strategy Ranking

- **Boundary-Aware**: 0.521
- **Semantic**: 0.478
- **Traditional Fixed-Size**: 0.008

### Metrics Comparison

| Strategy | Chunks | Avg Size | Boundary Score | Sentence Score |
|----------|--------|----------|----------------|---------------|
| Traditional Fixed-Size | 213 | 149.1 | 0.00 | 0.03 |
| Boundary-Aware | 11 | 819.0 | 0.73 | 0.04 |
| Semantic | 11 | 808.0 | 0.67 | 0.04 |

## Retrieval Method Comparison

### Retrieval with fixed_size chunking

Fastest method: **context**
Most unique results: **vector**

#### Retrieval Speed

- vector: 0.412s
- entity: 1.972s
- context: 0.001s
- hybrid: 0.006s

### Retrieval with boundary_aware chunking

Fastest method: **context**
Most unique results: **vector**

#### Retrieval Speed

- vector: 0.248s
- entity: 1.270s
- context: 0.001s
- hybrid: 0.004s

## Synthesis Method Comparison

