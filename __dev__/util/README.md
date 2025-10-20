# Qdrant Collection Inspection Utility

Utility scripts for inspecting and analyzing Qdrant collections.

## Scripts

### `inspect_collection.py`

Comprehensive inspection tool for Qdrant collections that retrieves and displays:

- **Collection Status**: Overall health and operational status
- **Statistics**: Point counts, vector counts, indexing progress
- **Vector Configuration**: Dense and sparse vector settings
- **Index Configuration**: HNSW parameters and indexing status
- **Payload Indexes**: Field-level indexing configuration
- **Optimizer Settings**: Memory, disk, and performance tuning
- **Replication & Sharding**: Distribution and consistency settings

## Usage

### Basic Inspection

```bash
# From project root
python __dev__/util/inspect_collection.py
```

The script will:
1. Connect to Qdrant using settings from `.env`
2. Retrieve information for both `ocr_chunks` and `ocr_summaries` collections
3. Display formatted reports in terminal for each collection
4. Optionally save detailed JSON output for all collections

### Example Output

```
🔍 Inspecting Qdrant collections: ocr_chunks, ocr_summaries

================================================================================
  Fetching info for: ocr_chunks
================================================================================

================================================================================
  Qdrant Collection Inspector - ocr_chunks
================================================================================
Timestamp: 2025-10-19 10:58:19
Qdrant URL: https://your-qdrant-instance.cloud.qdrant.io:6333

--------------------------------------------------------------------------------
  📊 Collection Status
--------------------------------------------------------------------------------
Status: green

--------------------------------------------------------------------------------
  📈 Statistics
--------------------------------------------------------------------------------
Total Points: 144
Total Vectors: 0
Indexed Vectors: 145
Segments Count: 2

--------------------------------------------------------------------------------
  🎯 Vector Configuration
--------------------------------------------------------------------------------

  Vector: ocr-dense-vector
    - Dimension: 1536
    - Distance Metric: Cosine
    - HNSW m: 0
    - HNSW ef_construct: 256
    - On-disk storage: True

  Sparse Vectors:
    - ocr-sparse-vector: Configured

[... additional sections ...]
```

### JSON Output

When prompted, you can save the complete information for all collections to a JSON file:

```
💾 Save detailed info to JSON file? (y/n): y
✅ Collections info saved to: __dev__/util/collections_info_20251019_105819.json
```

The JSON file contains a dictionary mapping collection names to their metadata with all nested configurations:
```json
{
  "ocr_chunks": { /* collection metadata */ },
  "ocr_summaries": { /* collection metadata */ }
}
```

## Key Metrics Explained

### Statistics

- **Total Points**: Number of documents/chunks stored
- **Total Vectors**: Combined count of all vector types
- **Indexed Vectors**: Vectors that have been indexed (HNSW)
- **Segments Count**: Number of storage segments

### Vector Configuration

- **Dimension**: Vector size (1536 for Gemini embeddings)
- **Distance Metric**: Similarity calculation method (Cosine, Euclidean, Dot)
- **HNSW m**: Max connections per layer in graph (higher = better recall, more memory)
- **HNSW ef_construct**: Construction quality (higher = better index, slower build)

### Indexing Status

Indexing progress shows what percentage of vectors have been indexed:
- 100% = All vectors indexed, optimal search performance
- <100% = Indexing in progress, may use full scan for some queries

**Note**: Qdrant uses lazy indexing based on `indexing_threshold` (default: 10000 KB). Small collections may show low indexing percentage by design.

### Optimizer Configuration

- **Indexing Threshold**: Minimum segment size (KB) before HNSW index is built
- **Deleted Threshold**: Fraction of deleted points triggering optimization
- **Flush Interval Sec**: How often to persist changes to disk

## Requirements

- Python 3.10+
- Dependencies from project `requirements.txt`:
  - `qdrant-client`
  - `pydantic-settings`
- Valid `.env` configuration with Qdrant credentials

## Environment Variables

Required variables (from project `.env`):

```env
QDRANT_URL=https://your-instance.cloud.qdrant.io:6333
QDRANT_MASTER_API_KEY=your-master-api-key
```

**Note**: The utility inspects both `ocr_chunks` and `ocr_summaries` collections by default. Collection names are hardcoded in the script.

## Troubleshooting

### Connection Errors

```
❌ Error retrieving collection info for 'ocr_chunks': ...
```

**Solutions**:
1. Verify `QDRANT_URL` and `QDRANT_MASTER_API_KEY` in `.env`
2. Check network connectivity to Qdrant instance
3. Confirm collections exist in your Qdrant instance

### Empty or Missing Data

If certain sections show "N/A" or 0 values:
- Collection may be newly created
- Indexing may be in progress
- Configuration may use default values

### Low Indexing Percentage

This is **normal** for small collections due to `indexing_threshold`. Qdrant only builds HNSW indexes when segments exceed the threshold size (default: 10000 KB).

## Use Cases

1. **Performance Debugging**: Check indexing status and HNSW parameters
2. **Configuration Audit**: Verify vector dimensions and distance metrics
3. **Capacity Planning**: Monitor point counts and segment distribution
4. **Troubleshooting**: Diagnose optimizer issues or indexing problems
5. **Documentation**: Generate snapshots of collection state for reference

## Integration

This utility can be integrated into:
- CI/CD pipelines for configuration validation
- Monitoring scripts for health checks
- Documentation generation workflows
- Debugging workflows during development

## Related Files

- `/app/qdrant_service.py`: Main Qdrant service implementation
- `/app/config.py`: Environment configuration
- `/app/embeddings.py`: Vector generation logic
- `CLAUDE.md`: Project documentation
