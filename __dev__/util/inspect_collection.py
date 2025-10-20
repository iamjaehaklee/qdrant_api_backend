"""
Qdrant Collection Inspection Utility

Retrieves and displays comprehensive information about Qdrant collections:
- Collection statistics (points, vectors, segments)
- Vector configurations (dense and sparse)
- Indexing status and parameters
- Payload schema and indexes
- Optimizer status

Inspects both ocr_chunks and ocr_summaries collections by default.

Usage:
    python __dev__/util/inspect_collection.py
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import AsyncQdrantClient
from pydantic_settings import BaseSettings, SettingsConfigDict


class InspectorSettings(BaseSettings):
    """Settings for the collection inspector"""
    qdrant_url: str
    qdrant_master_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Load settings
inspector_settings = InspectorSettings()


class CollectionInspector:
    """Inspector for Qdrant collection details"""

    def __init__(self, collection_names: list[str] = None):
        """
        Initialize Qdrant async client

        Args:
            collection_names: List of collection names to inspect.
                            Defaults to ["ocr_chunks", "ocr_summaries"]
        """
        self.client = AsyncQdrantClient(
            url=inspector_settings.qdrant_url,
            api_key=inspector_settings.qdrant_master_api_key,
            timeout=30.0
        )
        self.collection_names = collection_names or ["ocr_chunks", "ocr_summaries"]

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive collection information

        Args:
            collection_name: Name of the collection to inspect

        Returns:
            Dict containing collection details, config, and status
        """
        try:
            collection_info = await self.client.get_collection(
                collection_name=collection_name
            )
            # Convert to dict with all nested models
            return json.loads(collection_info.model_dump_json())
        except Exception as e:
            print(f"❌ Error retrieving collection info for '{collection_name}': {e}")
            return {}

    async def close(self):
        """Close the client connection"""
        await self.client.close()

    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} TB"

    def print_section(self, title: str, width: int = 80):
        """Print formatted section header"""
        print(f"\n{'=' * width}")
        print(f"  {title}")
        print(f"{'=' * width}")

    def print_subsection(self, title: str, width: int = 80):
        """Print formatted subsection header"""
        print(f"\n{'-' * width}")
        print(f"  {title}")
        print(f"{'-' * width}")

    def display_collection_info(self, collection_name: str, info: Dict[str, Any]):
        """
        Display formatted collection information

        Args:
            collection_name: Name of the collection
            info: Collection information dictionary
        """

        if not info:
            print(f"❌ No collection information available for '{collection_name}'")
            return

        # Header
        self.print_section(f"Qdrant Collection Inspector - {collection_name}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Qdrant URL: {inspector_settings.qdrant_url}")

        # Status Overview
        self.print_subsection("📊 Collection Status")
        status = info.get('status', 'unknown')
        print(f"Status: {status}")

        # Points and Vectors Statistics
        self.print_subsection("📈 Statistics")
        points_count = info.get('points_count') or 0
        vectors_count = info.get('vectors_count') or 0
        indexed_vectors_count = info.get('indexed_vectors_count') or 0
        segments_count = info.get('segments_count') or 0

        print(f"Total Points: {points_count:,}")
        print(f"Total Vectors: {vectors_count:,}")
        print(f"Indexed Vectors: {indexed_vectors_count:,}")
        print(f"Segments Count: {segments_count}")

        # Calculate indexing progress
        if vectors_count > 0:
            indexing_progress = (indexed_vectors_count / vectors_count) * 100
            print(f"Indexing Progress: {indexing_progress:.2f}%")

        # Vector Configuration
        self.print_subsection("🎯 Vector Configuration")
        config = info.get('config', {})
        params = config.get('params', {})
        vectors_config = params.get('vectors', {})

        if isinstance(vectors_config, dict):
            for vector_name, vector_config in vectors_config.items():
                print(f"\n  Vector: {vector_name}")
                if isinstance(vector_config, dict):
                    size = vector_config.get('size', 'N/A')
                    distance = vector_config.get('distance', 'N/A')
                    print(f"    - Dimension: {size}")
                    print(f"    - Distance Metric: {distance}")

                    # HNSW Configuration
                    hnsw_config = vector_config.get('hnsw_config', {})
                    if hnsw_config:
                        print(f"    - HNSW m: {hnsw_config.get('m', 'N/A')}")
                        print(f"    - HNSW ef_construct: {hnsw_config.get('ef_construct', 'N/A')}")
                        print(f"    - HNSW full_scan_threshold: {hnsw_config.get('full_scan_threshold', 'N/A')}")

                    # Quantization
                    quantization_config = vector_config.get('quantization_config')
                    if quantization_config:
                        print(f"    - Quantization: Enabled ({type(quantization_config).__name__})")

                    # On-disk storage
                    on_disk = vector_config.get('on_disk', False)
                    print(f"    - On-disk storage: {on_disk}")

        # Sparse Vectors Configuration
        sparse_vectors_config = params.get('sparse_vectors')
        if sparse_vectors_config:
            print(f"\n  Sparse Vectors:")
            if isinstance(sparse_vectors_config, dict):
                for sparse_name, sparse_config in sparse_vectors_config.items():
                    print(f"    - {sparse_name}: Configured")

        # Payload Schema and Indexes
        self.print_subsection("🗂️  Payload Indexes")
        payload_schema = config.get('params', {}).get('payload_schema', {})

        if payload_schema:
            print("Indexed Fields:")
            for field_name, field_config in payload_schema.items():
                field_type = field_config.get('data_type', 'unknown')
                print(f"  - {field_name}: {field_type}")
        else:
            print("No explicit payload indexes configured (auto-indexing enabled)")

        # Optimizer Configuration
        self.print_subsection("⚙️  Optimizer Configuration")
        optimizer_config = config.get('optimizer_config', {})
        if optimizer_config:
            print(f"Deleted Threshold: {optimizer_config.get('deleted_threshold', 'N/A')}")
            print(f"Vacuum Min Vector Number: {optimizer_config.get('vacuum_min_vector_number', 'N/A')}")
            print(f"Default Segment Number: {optimizer_config.get('default_segment_number', 'N/A')}")
            print(f"Max Segment Size: {optimizer_config.get('max_segment_size', 'N/A')}")
            print(f"Memmap Threshold: {optimizer_config.get('memmap_threshold', 'N/A')}")
            print(f"Indexing Threshold: {optimizer_config.get('indexing_threshold', 'N/A')} KB")
            print(f"Flush Interval Sec: {optimizer_config.get('flush_interval_sec', 'N/A')}")
            print(f"Max Optimization Threads: {optimizer_config.get('max_optimization_threads', 'N/A')}")

        # Optimizer Status
        optimizer_status = info.get('optimizer_status', {})
        if optimizer_status:
            if isinstance(optimizer_status, dict):
                status_value = optimizer_status.get('status', 'unknown')
                print(f"\nOptimizer Status: {status_value}")

                if optimizer_status.get('error'):
                    print(f"⚠️  Optimizer Error: {optimizer_status.get('error')}")
            else:
                # If it's a string or other type, just print it
                print(f"\nOptimizer Status: {optimizer_status}")

        # HNSW Configuration
        self.print_subsection("🔍 HNSW Index Configuration")
        hnsw_config = config.get('hnsw_config', {})
        if hnsw_config:
            print(f"m (max connections per layer): {hnsw_config.get('m', 'N/A')}")
            print(f"ef_construct (construction time): {hnsw_config.get('ef_construct', 'N/A')}")
            print(f"full_scan_threshold: {hnsw_config.get('full_scan_threshold', 'N/A')}")
            print(f"max_indexing_threads: {hnsw_config.get('max_indexing_threads', 'N/A')}")
            print(f"on_disk: {hnsw_config.get('on_disk', False)}")

        # Write-Ahead Log (WAL)
        self.print_subsection("📝 Write-Ahead Log Configuration")
        wal_config = config.get('wal_config', {})
        if wal_config:
            print(f"WAL Capacity MB: {wal_config.get('wal_capacity_mb', 'N/A')}")
            print(f"WAL Segments Ahead: {wal_config.get('wal_segments_ahead', 'N/A')}")

        # Replication and Sharding
        self.print_subsection("🔄 Replication & Sharding")
        replication_factor = params.get('replication_factor', 1)
        write_consistency_factor = params.get('write_consistency_factor', 1)
        shard_number = params.get('shard_number', 1)

        print(f"Replication Factor: {replication_factor}")
        print(f"Write Consistency Factor: {write_consistency_factor}")
        print(f"Shard Number: {shard_number}")

        # Footer
        self.print_section("End of Report")
        print()

    async def save_to_json(self, all_info: Dict[str, Dict[str, Any]], output_path: str = None):
        """
        Save all collections info to JSON file

        Args:
            all_info: Dictionary mapping collection names to their information
            output_path: Output file path (optional)
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"__dev__/util/collections_info_{timestamp}.json"

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_info, f, indent=2, ensure_ascii=False)
            print(f"✅ Collections info saved to: {output_path}")
        except Exception as e:
            print(f"❌ Error saving to JSON: {e}")


async def main():
    """Main execution function"""
    inspector = CollectionInspector()

    try:
        print(f"🔍 Inspecting Qdrant collections: {', '.join(inspector.collection_names)}\n")

        all_info = {}

        # Inspect each collection
        for collection_name in inspector.collection_names:
            print(f"\n{'=' * 80}")
            print(f"  Fetching info for: {collection_name}")
            print(f"{'=' * 80}\n")

            info = await inspector.get_collection_info(collection_name)

            if info:
                all_info[collection_name] = info
                inspector.display_collection_info(collection_name, info)
            else:
                print(f"❌ Failed to retrieve information for '{collection_name}'")
                all_info[collection_name] = {"error": "Failed to retrieve information"}

        # Optionally save to JSON
        if all_info:
            save_json = input("\n💾 Save detailed info to JSON file? (y/n): ").lower().strip()
            if save_json == 'y':
                await inspector.save_to_json(all_info)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        await inspector.close()
        print("\n✅ Inspection complete")


if __name__ == "__main__":
    asyncio.run(main())
