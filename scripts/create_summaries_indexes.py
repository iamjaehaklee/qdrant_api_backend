"""
Create Payload Indexes for ocr_summaries Collection

This script creates integer indexes for project_id and file_id fields
to enable efficient filtering in search operations.

Usage:
    python scripts/create_summaries_indexes.py
"""

import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PayloadSchemaType

QDRANT_URL = "https://6210ba2b-aca2-46ad-b205-7ebc58dd3641.us-east-1-0.aws.cloud.qdrant.io:6333"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.95VjftkJBIA1QG2wVp3Mwb0KT52mM7Q-Cm7xIEVkNZY"
COLLECTION = "ocr_summaries"


async def create_indexes():
    """Create payload indexes for ocr_summaries collection"""
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=API_KEY, timeout=60.0)

    print(f"Creating indexes for {COLLECTION} collection...")
    print("=" * 60)

    try:
        # 1. project_id 인덱스 (INTEGER)
        print("\n[1/2] Creating index for project_id (INTEGER)...")
        await client.create_payload_index(
            collection_name=COLLECTION,
            field_name="project_id",
            field_schema=PayloadSchemaType.INTEGER
        )
        print("✅ project_id index created successfully")

        # 2. file_id 인덱스 (INTEGER)
        print("\n[2/2] Creating index for file_id (INTEGER)...")
        await client.create_payload_index(
            collection_name=COLLECTION,
            field_name="file_id",
            field_schema=PayloadSchemaType.INTEGER
        )
        print("✅ file_id index created successfully")

        print("\n" + "=" * 60)
        print("✅ All indexes created successfully!")
        print("=" * 60)

        # 확인
        print("\n📋 Verifying payload schema...")
        info = await client.get_collection(COLLECTION)

        if info.payload_schema:
            print("\nPayload Schema:")
            for field_name, schema in info.payload_schema.items():
                points_count = getattr(schema, 'points', 'N/A')
                data_type = getattr(schema, 'data_type', 'N/A')
                print(f"  - {field_name}: {data_type} ({points_count} points)")

        print("\n✅ Index creation completed!")

    except Exception as e:
        print(f"\n❌ Error creating indexes: {e}")
        raise
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(create_indexes())
