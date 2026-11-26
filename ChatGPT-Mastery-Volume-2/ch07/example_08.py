class NormalizedBoundingBox(BaseModel):
      top_y: int = Field(ge=0, le=1000, description="Top-most Y coordinate (0-1000)")
      left_x: int = Field(ge=0, le=1000, description="Left-most X coordinate (0-1000)")
      bottom_y: int = Field(ge=0, le=1000, description="Bottom-most Y coordinate (0-1000)")
      right_x: int = Field(ge=0, le=1000, description="Right-most X coordinate (0-1000)")
  ```
  Named keys eliminate indexing ambiguity entirely, guaranteeing mathematical reliability.

---

## 15. Comparative Decision Matrix: Visual Processing Architectures

| Visual Processing Paradigm | Traditional OCR (Tesseract / AWS Textract) | Specialized VDU (LayoutLMv3) | GPT-4o Vision API | Self-Hosted Open Vision (LLaVA / Qwen2-VL) |
| :--- | :--- | :--- | :--- | :--- |
| **Spatial Document Layout** | Poor (Linear text dump) | **High (Bounding box tuning)** | **Superior (Deep Visual Reasoning)**| Moderate to High |
| **Reasoning over Charts & Trends**| None | None | **Superior (Trend extrapolation)** | Moderate |
| **Multilingual Handwritten Text** | Poor | Moderate | **High (Zero-shot OCR)** | Moderate |
| **Engineering Blueprint Parsing** | Ineffective | Poor | **Superior (Spatial relationships)** | Moderate |
| **Setup & Training Overhead** | Low (Off-the-shelf) | High (Requires custom labeling) | **Instant (Zero Training Required)**| Moderate (GPU hosting) |
| **Cost per 1,000 Pages** | $1.50–$3.00 | $10.00 (Self-hosted compute) | **$2.50–$3.50 (Predictable)** | $2.00 (GPU infrastructure) |
| **Optimal Enterprise Use Case**| Plain text scanned book OCR | High-volume standardized tax forms| Complex invoices, charts, schematics| Air-gapped defense / on-premises |

---

## 16. Multimodal Vector Search & CLIP Embedding Topologies

### 16.1 Contrastive Vision-Language Pre-Training (CLIP)
Before multimodal foundation models could generate conversational answers about images, they required a mathematical bridge connecting visual pixels with natural language semantics.

Radford et al. (2021) introduced **CLIP (Contrastive Language-Image Pre-training)**, which trains a separate Vision Encoder $f_{\theta}(I)$ and Text Encoder $g_{\phi}(T)$ to map images and text into a shared, joint $d$-dimensional embedding space:


![Figure 7.12: CLIP Contrastive Embedding Alignment](../assets/svg/diag_ch07_sec_08_clip_contrastive_alignment.svg)


The model is trained on batches of $B$ image-text pairs using symmetric contrastive cross-entropy loss:

$$\mathcal{L}_{\text{CLIP}} = \frac{1}{2} \left( \mathcal{L}_{I \to T} + \mathcal{L}_{T \to I} \right)$$

$$\mathcal{L}_{I \to T} = -\frac{1}{B} \sum_{i=1}^B \log \frac{\exp\left( \frac{\langle f(I_i), g(T_i) \rangle}{\tau} \right)}{\sum_{j=1}^B \exp\left( \frac{\langle f(I_i), g(T_j) \rangle}{\tau} \right)}$$

$$\mathcal{L}_{T \to I} = -\frac{1}{B} \sum_{i=1}^B \log \frac{\exp\left( \frac{\langle g(T_i), f(I_i) \rangle}{\tau} \right)}{\sum_{j=1}^B \exp\left( \frac{\langle g(T_i), f(I_j) \rangle}{\tau} \right)}$$

Where $\tau$ is a learnable temperature parameter controlling the sharpness of the probability distribution.

### 16.2 Production Multimodal Visual RAG Architecture
In high-scale enterprise image archives (such as millions of construction site safety photos or e-commerce catalog items), calling GPT-4o Vision on every single image to answer user questions is mathematically impossible ($1,000,000 \times \$0.002 = \$2,000$ per user query!).

Enterprise architectures implement **Two-Stage Multimodal Visual RAG**:
1. **Stage 1 (Sub-Millisecond Vector Retrieval)**:
   * Ingest images through a CLIP vision encoder to generate 512-dimensional vectors.
   * Index vectors into Qdrant or Pinecone.
   * When a user searches (*"Forklifts operating without amber warning lights"*), encode the query with the CLIP text encoder and perform approximate nearest neighbor (ANN) cosine search.
   * Return the top-5 candidate image IDs in **8 milliseconds**.
2. **Stage 2 (Deep Multimodal Synthesis)**:
   * Fetch only the top-5 candidate images from S3.
   * Submit the 5 retrieved images to GPT-4o Vision with structured Pydantic schemas to generate the final analytical report.

---

## 17. High-Precision Engineering Schematics & Hierarchical ROI Slicing

### 17.1 The Sub-Pixel Challenge in Technical Blueprints
While standard 1080p photographs downscale cleanly to the 768px shortest-side constraint of GPT-4o Vision, **industrial technical schematics** (Piping & Instrumentation Diagrams, multi-layer printed circuit boards, architectural blueprints) operate at extreme resolutions ($10,000 \times 7,000$ pixels at 300 DPI).

Downscaling a $10,000 \times 7,000$ blueprint to $768$px destroys critical engineering details:
* Wire gauge numbers (`14-AWG` vs `12-AWG`) become indistinguishable gray smudges.
* Valve status glyphs (normally open vs normally closed) lose their internal hash marks.
* Decimal points in engineering tolerances ($0.005$mm vs $0.05$mm) disappear.

### 17.2 Hierarchical Region-of-Interest (ROI) Ingestion Pipeline
To analyze massive schematics with zero loss of sub-millimeter precision, production systems implement **Hierarchical Region-of-Interest (ROI) Slicing**:


![Figure 7.13: Hierarchical ROI Slicing Topology](../assets/svg/diag_ch07_sec_09_hierarchical_roi_slicing.svg)


By separating global macroscopic orientation from local microscopic inspection, the architecture preserves absolute optical fidelity while keeping token budgets strictly bounded.

### 17.3 Production Python Implementation: Overlapping Grid Blueprint Slicer
When cutting massive schematics into sub-tiles, slicing strictly along grid seams risks cutting text characters or circuit symbols directly in half.

Production systems enforce **Overlapping Tiling with Coordinate Re-Mapping**:
