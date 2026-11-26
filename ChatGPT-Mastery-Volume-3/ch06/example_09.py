# multimodal_azure_search_indexer.py — Dual-Modality Search Pipeline
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile
)

class MultimodalSearchManager:
    def __init__(self, endpoint: str, key: str, index_name: str = "idx-multimodal-enterprise"):
        self.endpoint = endpoint
        self.cred = AzureKeyCredential(key)
        self.index_name = index_name
        self.index_client = SearchIndexClient(endpoint=endpoint, credential=self.cred)

    def create_dual_vector_index(self):
        """Creates Azure AI Search index with distinct Text and Vision vector fields."""
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="doc_id", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="image_caption", type=SearchFieldDataType.String),
            # Text Vector: 3072 dims (text-embedding-3-large)
            SearchField(
                name="text_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=3072,
                vector_search_profile_name="hnsw-profile"
            ),
            # Image Vector: 1024 dims (CLIP ViT-Large)
            SearchField(
                name="image_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1024,
                vector_search_profile_name="hnsw-profile"
            ),
            SimpleField(name="image_url", type=SearchFieldDataType.String)
        ]

        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo", m=16, ef_construction=400)],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")]
        )

        index = SearchIndex(name=self.index_name, fields=fields, vector_search=vector_search)
        self.index_client.create_or_update_index(index)
        print(f"Dual-Modality Vector Search Index created: {self.index_name}")
