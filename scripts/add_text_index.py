"""
Add Text Index to Qdrant Collections
Adds text index to paragraph_texts (ocr_chunks) and summary_text (ocr_summaries) fields
"""

import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import TextIndexParams, PayloadSchemaType
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings


async def add_text_indexes():
    """Add text indexes to both collections"""

    # Create Qdrant client
    client = AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_master_api_key,
        timeout=30.0
    )

    print("=" * 60)
    print("Adding Text Indexes to Qdrant Collections")
    print("=" * 60)

    # Text index configuration
    text_index_params = TextIndexParams(
        type=PayloadSchemaType.TEXT,
        tokenizer="multilingual",
        lowercase=True,
        min_token_len=2,
        max_token_len=20
    )

    # Add text index to ocr_chunks.paragraph_texts
    print("\n1. Adding text index to ocr_chunks.paragraph_texts...")
    try:
        await client.create_payload_index(
            collection_name="ocr_chunks",
            field_name="paragraph_texts",
            field_schema=text_index_params
        )
        print("   ✅ Text index added to ocr_chunks.paragraph_texts")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"   ℹ️  Text index already exists on ocr_chunks.paragraph_texts")
        else:
            print(f"   ❌ Error: {str(e)}")
            raise

    # Add text index to ocr_summaries.summary_text
    print("\n2. Adding text index to ocr_summaries.summary_text...")
    try:
        await client.create_payload_index(
            collection_name="ocr_summaries",
            field_name="summary_text",
            field_schema=text_index_params
        )
        print("   ✅ Text index added to ocr_summaries.summary_text")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"   ℹ️  Text index already exists on ocr_summaries.summary_text")
        else:
            print(f"   ❌ Error: {str(e)}")
            raise

    # Verify indexes
    print("\n" + "=" * 60)
    print("Verifying Indexes")
    print("=" * 60)

    # Get ocr_chunks collection info
    print("\n1. ocr_chunks collection:")
    try:
        chunks_info = await client.get_collection("ocr_chunks")
        if chunks_info.payload_schema:
            for field_name, field_info in chunks_info.payload_schema.items():
                if field_name == "paragraph_texts":
                    print(f"   ✅ paragraph_texts index: {field_info}")
        else:
            print("   ℹ️  No payload schema found")
    except Exception as e:
        print(f"   ❌ Error getting collection info: {str(e)}")

    # Get ocr_summaries collection info
    print("\n2. ocr_summaries collection:")
    try:
        summaries_info = await client.get_collection("ocr_summaries")
        if summaries_info.payload_schema:
            for field_name, field_info in summaries_info.payload_schema.items():
                if field_name == "summary_text":
                    print(f"   ✅ summary_text index: {field_info}")
        else:
            print("   ℹ️  No payload schema found")
    except Exception as e:
        print(f"   ❌ Error getting collection info: {str(e)}")

    print("\n" + "=" * 60)
    print("Text Index Addition Complete!")
    print("=" * 60)
    print("\nText indexes enable fast MatchText searches:")
    print("- ocr_chunks: /search/matchtext")
    print("- ocr_summaries: /summaries/search/matchtext")
    print("\nMatchText searches do NOT use Kiwi morphological analysis.")
    print("They search text as-is for exact phrase matching.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(add_text_indexes())
