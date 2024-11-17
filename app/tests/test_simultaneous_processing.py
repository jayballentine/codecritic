import pytest
import asyncio
from app.intake.code_extraction import CodeExtractor
from app.main import process_initial_reviews, process_batch_reviews

def test_repository_hierarchy_preservation():
    """
    Ensure repository hierarchy is preserved through processing
    """
    extractor = CodeExtractor()
    files = list(extractor.stream_github_files('https://github.com/jayballentine/codecritic'))
    
    # Check that each file has repository hierarchy
    for file in files:
        assert 'repository_hierarchy' in file.__dict__, f"Missing hierarchy for {file.path}"
        assert file.repository_hierarchy.get('owner') == 'jayballentine'
        assert file.repository_hierarchy.get('repo') == 'codecritic'
        assert file.repository_hierarchy.get('branch') == 'main'

@pytest.mark.asyncio
async def test_concurrent_file_processing():
    """
    Test that files are processed concurrently with minimal total processing time
    """
    extractor = CodeExtractor()
    files = list(extractor.stream_github_files('https://github.com/jayballentine/codecritic'))[:10]  # Test with exactly 10 files
    
    start_time = asyncio.get_event_loop().time()
    
    # Process files concurrently
    reviews = await process_initial_reviews(files, "claude-3-haiku-20240307")
    
    end_time = asyncio.get_event_loop().time()
    processing_time = end_time - start_time
    
    # Validate results
    assert len(reviews) == 10, "Must process exactly 10 files"
    # Allow 2 seconds per file for API latency when concurrent
    assert processing_time < 20, "Processing was not concurrent"

@pytest.mark.asyncio
async def test_batch_processing():
    """
    Test that batch reviews are processed simultaneously
    """
    extractor = CodeExtractor()
    files = list(extractor.stream_github_files('https://github.com/jayballentine/codecritic'))[:10]  # Test with exactly 10 files
    
    # Get initial reviews
    initial_reviews = await process_initial_reviews(files, "claude-3-haiku-20240307")
    
    assert len(initial_reviews) == 10, "Must have exactly 10 files for batch"
    
    start_time = asyncio.get_event_loop().time()
    batch_reviews = await process_batch_reviews(initial_reviews, "claude-3-haiku-20240307")
    end_time = asyncio.get_event_loop().time()
    
    processing_time = end_time - start_time
    
    # Validate results
    assert len(batch_reviews) > 0, "No batch reviews generated"
    # Allow 20 seconds for batch of 10 files when processed concurrently
    assert processing_time < 20, f"Batch processing took too long: {processing_time:.2f}s"
