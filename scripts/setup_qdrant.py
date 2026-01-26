"""
Initialize Qdrant and index templates using trigger queries.

This script indexes templates by their trigger_queries field rather than
template text. This creates query-to-query semantic matching instead of
query-to-answer matching, which produces much higher similarity scores.
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
    """Load and index templates in Qdrant using trigger queries."""
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

    # Expand templates into trigger query entries
    # Each trigger query becomes a separate point in Qdrant
    trigger_entries = []
    for template in templates:
        trigger_queries = template.get("trigger_queries", [])
        if not trigger_queries:
            # Fallback: use template text if no trigger queries defined
            trigger_entries.append({
                "template_id": template["id"],
                "category": template["category"],
                "text": template["text"],
                "metadata": template["metadata"],
                "trigger_query": template["text"],  # Use text as trigger
            })
        else:
            for query in trigger_queries:
                trigger_entries.append({
                    "template_id": template["id"],
                    "category": template["category"],
                    "text": template["text"],
                    "metadata": template["metadata"],
                    "trigger_query": query,
                })

    print(f"Expanded to {len(trigger_entries)} trigger query entries")

    # Generate embeddings in batches
    print("Generating embeddings for trigger queries...")
    batch_size = 100
    all_points = []

    for i in range(0, len(trigger_entries), batch_size):
        batch = trigger_entries[i:i + batch_size]
        # Embed the trigger queries, not the template text
        texts = [entry["trigger_query"] for entry in batch]

        embeddings = await generate_embeddings(texts)

        # Create points
        for j, (entry, embedding) in enumerate(zip(batch, embeddings)):
            point = PointStruct(
                id=i + j,
                vector=embedding,
                payload={
                    "template_id": entry["template_id"],
                    "category": entry["category"],
                    "text": entry["text"],
                    "metadata": entry["metadata"],
                    "trigger_query": entry["trigger_query"],
                },
            )
            all_points.append(point)

        print(f"Processed {i + len(batch)}/{len(trigger_entries)} trigger queries")

    # Upsert all points
    print("Indexing trigger queries in Qdrant...")
    await upsert_points(
        collection_name=settings.qdrant_collection_name,
        points=all_points,
    )

    print(f"\n✓ Successfully indexed {len(trigger_entries)} trigger queries from {len(templates)} templates!")


def main():
    """Main entry point."""
    asyncio.run(index_templates())


if __name__ == "__main__":
    main()
