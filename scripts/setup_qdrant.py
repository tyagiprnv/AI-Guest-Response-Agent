"""
Initialize Qdrant and index templates.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from qdrant_client.models import PointStruct

from src.config.settings import get_settings
from src.retrieval.embeddings import generate_embeddings
from src.retrieval.qdrant_client import create_collection, upsert_points

DATA_DIR = BASE_DIR / "data"


async def index_templates():
    """Load and index templates in Qdrant."""
    settings = get_settings()

    # Create collection
    print(f"Creating collection '{settings.qdrant_collection_name}'...")
    create_collection(
        collection_name=settings.qdrant_collection_name,
        vector_size=settings.embedding_dimension,
    )

    # Load templates
    templates_file = DATA_DIR / "templates" / "response_templates.jsonl"
    if not templates_file.exists():
        print("Error: Templates file not found. Run generate_synthetic_data.py first.")
        return

    print("Loading templates...")
    templates = []
    with open(templates_file, "r") as f:
        for line in f:
            templates.append(json.loads(line))

    print(f"Loaded {len(templates)} templates")

    # Generate embeddings in batches
    print("Generating embeddings...")
    batch_size = 100
    all_points = []

    for i in range(0, len(templates), batch_size):
        batch = templates[i:i + batch_size]
        texts = [t["text"] for t in batch]

        embeddings = await generate_embeddings(texts)

        # Create points
        for j, (template, embedding) in enumerate(zip(batch, embeddings)):
            point = PointStruct(
                id=i + j,
                vector=embedding,
                payload={
                    "template_id": template["id"],
                    "category": template["category"],
                    "text": template["text"],
                    "metadata": template["metadata"],
                },
            )
            all_points.append(point)

        print(f"Processed {i + len(batch)}/{len(templates)} templates")

    # Upsert all points
    print("Indexing templates in Qdrant...")
    await upsert_points(
        collection_name=settings.qdrant_collection_name,
        points=all_points,
    )

    print(f"\n✓ Successfully indexed {len(templates)} templates!")


def main():
    """Main entry point."""
    asyncio.run(index_templates())


if __name__ == "__main__":
    main()
