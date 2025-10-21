"""
Executors
Configurable thread/process pools for CPU-bound offloading
"""

from __future__ import annotations

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Optional

from app.config import settings

# Global executor used for sparse embedding offloading
sparse_executor: Optional[ThreadPoolExecutor | ProcessPoolExecutor] = None


def _auto_thread_workers() -> int:
    cpu = max(1, multiprocessing.cpu_count())
    return min(32, cpu * 2)


def _auto_process_workers() -> int:
    return max(1, multiprocessing.cpu_count())


def _warmup_sparse_embedder() -> None:
    """Optional: warm up multilingual sparse embedder in child worker."""
    try:
        from app.multilingual_sparse_embedding import create_multilingual_sparse_embedding
        # Small warm-up to initialize Kiwi / FastEmbed paths
        create_multilingual_sparse_embedding("워밍업 warmup text")
    except Exception:
        # Warmup is best-effort; ignore failures to avoid crashing workers
        pass


def init_executors() -> None:
    global sparse_executor
    kind = (settings.sparse_offload_executor or "thread").lower()

    if kind == "process":
        workers = settings.cpu_processpool_workers or _auto_process_workers()
        sparse_executor = ProcessPoolExecutor(
            max_workers=workers,
            initializer=_warmup_sparse_embedder,
        )
    else:
        workers = settings.cpu_threadpool_workers or _auto_thread_workers()
        sparse_executor = ThreadPoolExecutor(
            max_workers=workers,
            thread_name_prefix="sparse-offload",
        )


def shutdown_executors() -> None:
    global sparse_executor
    if sparse_executor is not None:
        try:
            sparse_executor.shutdown(wait=True, cancel_futures=True)
        finally:
            sparse_executor = None

