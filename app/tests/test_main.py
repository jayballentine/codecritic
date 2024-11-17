import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import main, get_github_url
from app.intake.code_extraction import CodeExtractor, ExtractedFile

@pytest.fixture
def mock_code_extractor():
    with patch('app.main.CodeExtractor') as mock:
        instance = mock.return_value
        # Mock the stream_github_files method to return a sample file
        instance.stream_github_files.return_value = [
            ExtractedFile(
                path="test.py",
                content="print('test')",
                language="Python",
                size=100
            )
        ]
        yield instance

@pytest.mark.asyncio
async def test_get_github_url_valid():
    """Test valid GitHub URL input"""
    with patch('builtins.input', return_value='https://github.com/user/repo'):
        url = await get_github_url()
        assert url == 'https://github.com/user/repo'

@pytest.mark.asyncio
async def test_get_github_url_invalid_format():
    """Test invalid GitHub URL format"""
    with patch('builtins.input', return_value='not-a-url'):
        with pytest.raises(ValueError, match="URL must be from github.com"):
            await get_github_url()

@pytest.mark.asyncio
async def test_get_github_url_invalid_github_format():
    """Test invalid GitHub URL format but with github.com domain"""
    with patch('builtins.input', return_value='https://github.com/invalid-format'):
        with pytest.raises(ValueError, match="Invalid GitHub URL format"):
            await get_github_url()

@pytest.mark.asyncio
async def test_get_github_url_non_github():
    """Test non-GitHub URL input"""
    with patch('builtins.input', return_value='https://gitlab.com/user/repo'):
        with pytest.raises(ValueError, match="URL must be from github.com"):
            await get_github_url()

@pytest.mark.asyncio
async def test_main_with_valid_url(mock_code_extractor):
    """Test main function with valid GitHub URL"""
    with patch('app.main.get_github_url', return_value='https://github.com/user/repo'), \
         patch('app.main.Review') as mock_review, \
         patch('app.main.process_initial_reviews', new_callable=AsyncMock) as mock_initial, \
         patch('app.main.process_batch_reviews', new_callable=AsyncMock) as mock_batch, \
         patch('app.main.process_merged_review', new_callable=AsyncMock) as mock_merged, \
         patch('app.main.process_final_review', new_callable=AsyncMock) as mock_final:
        
        # Configure mocks
        mock_review.create.return_value = MagicMock()
        mock_initial.return_value = []
        mock_batch.return_value = []
        mock_merged.return_value = "merged review"
        mock_final.return_value = "final review"

        # Run main
        await main()

        # Verify CodeExtractor was called with the correct URL
        mock_code_extractor.stream_github_files.assert_called_once_with('https://github.com/user/repo')

@pytest.mark.asyncio
async def test_main_with_private_repo(mock_code_extractor):
    """Test main function with private repository"""
    mock_code_extractor.stream_github_files.side_effect = Exception("Not authorized")
    
    with patch('app.main.get_github_url', return_value='https://github.com/user/private-repo'), \
         pytest.raises(Exception, match="Not authorized"):
        await main()

@pytest.mark.asyncio
async def test_main_with_nonexistent_repo(mock_code_extractor):
    """Test main function with non-existent repository"""
    mock_code_extractor.stream_github_files.side_effect = Exception("Repository not found")
    
    with patch('app.main.get_github_url', return_value='https://github.com/user/nonexistent'), \
         pytest.raises(Exception, match="Repository not found"):
        await main()
