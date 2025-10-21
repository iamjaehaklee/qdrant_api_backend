# Health Endpoints

Health check and collection information endpoints for monitoring service status.

## Table of Contents
- [Health Check](#health-check)
- [Collection Info](#collection-info)

---

## Health Check

Check Qdrant connection and collection status.

### Endpoint

```
GET /health
```

### Response Model

**HealthResponse**

| Field | Type | Description |
|-------|------|-------------|
| status | string | Health status: "healthy" or "unhealthy" |
| qdrant_connected | boolean | Qdrant connection status |
| collection_exists | boolean | Whether collection exists |
| message | string \| null | Error message if unhealthy |

### Example Request

```bash
curl -X GET "http://localhost:8000/health"
```

### Example Response

**Success (Healthy)**

```json
{
  "status": "healthy",
  "qdrant_connected": true,
  "collection_exists": true,
  "message": null
}
```

**Failure (Unhealthy)**

```json
{
  "status": "unhealthy",
  "qdrant_connected": false,
  "collection_exists": false,
  "message": "Connection to Qdrant failed"
}
```

### Status Codes

- `200 OK`: Health check completed (check status field for actual health)

---

## Collection Info

Get detailed information about the Qdrant collection.

### Endpoint

```
GET /collection/info
```

### Response Model

**CollectionInfoResponse**

| Field | Type | Description |
|-------|------|-------------|
| status | string | Collection status |
| vectors_count | integer | Total number of vectors |
| points_count | integer | Total number of points |
| segments_count | integer | Number of segments |
| config | object | Collection configuration |

### Example Request

```bash
curl -X GET "http://localhost:8000/collection/info"
```

### Example Response

```json
{
  "status": "green",
  "vectors_count": 1523,
  "points_count": 1523,
  "segments_count": 3,
  "config": {
    "params": {
      "vectors": {
        "ocr-dense-vector": {
          "size": 1536,
          "distance": "Cosine"
        },
        "ocr-sparse-vector": {
          "sparse": true
        }
      }
    }
  }
}
```

### Status Codes

- `200 OK`: Collection info retrieved successfully
- `500 Internal Server Error`: Failed to retrieve collection info

### Error Response

```json
{
  "detail": "Failed to get collection info: [error details]"
}
```

---

## Use Cases

### 1. Health Monitoring

Monitor service health in production:

```bash
#!/bin/bash
# health_check.sh

RESPONSE=$(curl -s http://localhost:8000/health)
STATUS=$(echo $RESPONSE | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
  echo "Service is healthy"
  exit 0
else
  echo "Service is unhealthy: $RESPONSE"
  exit 1
fi
```

### 2. Collection Statistics

Check collection size before operations:

```bash
curl -s http://localhost:8000/collection/info | jq '.points_count'
```

### 3. Pre-deployment Verification

```python
import requests

def verify_service_ready():
    """Verify service is ready before deployment"""
    health = requests.get("http://localhost:8000/health").json()

    if not health["qdrant_connected"]:
        raise Exception("Qdrant not connected")

    if not health["collection_exists"]:
        raise Exception("Collection does not exist")

    info = requests.get("http://localhost:8000/collection/info").json()
    print(f"Collection ready: {info['points_count']} points")

    return True
```

---

## Related Endpoints

- [Overview](./01_overview.md)
- [Points Endpoints](./03_points_endpoints.md)
