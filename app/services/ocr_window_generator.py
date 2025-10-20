"""
OCR Window Generator
Creates 3-page sliding windows with 1-page overlap for OCR chunking
"""

from typing import List


class OCRWindowGenerator:
    """
    Generates 3-page sliding windows for OCR chunk creation

    Example for 14 pages:
    - Window 1: [1, 2, 3]
    - Window 2: [3, 4, 5]
    - Window 3: [5, 6, 7]
    - Window 4: [7, 8, 9]
    - Window 5: [9, 10, 11]
    - Window 6: [11, 12, 13]
    - Window 7: [13, 14]
    """

    def create_windows(self, total_pages: int) -> List[List[int]]:
        """
        Create 3-page sliding windows with 1-page overlap

        Args:
            total_pages: Total number of pages in document

        Returns:
            List of windows, where each window is a list of page numbers (1-indexed)

        Example:
            >>> generator = OCRWindowGenerator()
            >>> generator.create_windows(14)
            [[1, 2, 3], [3, 4, 5], [5, 6, 7], [7, 8, 9], [9, 10, 11], [11, 12, 13], [13, 14]]
        """
        if total_pages <= 0:
            return []

        windows = []

        # Create windows with 2-step increment (1-page overlap)
        for start in range(1, total_pages + 1, 2):
            end = min(start + 2, total_pages)
            window = list(range(start, end + 1))
            windows.append(window)

            # Stop if we've reached the last page
            if end >= total_pages:
                break

        return windows

    def get_window_count(self, total_pages: int) -> int:
        """
        Calculate how many windows will be created

        Args:
            total_pages: Total number of pages

        Returns:
            Number of windows
        """
        return len(self.create_windows(total_pages))
