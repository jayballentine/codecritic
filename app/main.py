import os
import logging
import asyncio
import aiohttp
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic
from app.intake.code_extraction import CodeExtractor
from app.models.review import Review
from rich.console import Console

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

# Load environment variables
load_dotenv()

# Initialize Anthropic client
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def get_github_url() -> str:
    """
    Get and validate GitHub repository URL from user input.
    
    Returns:
        str: Validated GitHub repository URL
        
    Raises:
        ValueError: If URL format is invalid or not from github.com
    """
    url = input("Enter GitHub repository URL: ").strip()
    
    # First check if it's a GitHub URL
    if not url.startswith('https://github.com/'):
        raise ValueError("URL must be from github.com")
        
    # Then validate the format
    github_pattern = r'^https://github\.com/[\w-]+/[\w-]+/?$'
    if not re.match(github_pattern, url):
        raise ValueError("Invalid GitHub URL format")
    
    return url

async def async_create_message(prompt, model):
    """Async wrapper for Anthropic API calls"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            }
        ) as response:
            result = await response.json()
            return result['content'][0]['text']

async def process_single_file(file, model, initial_prompt, timestamp):
    """Process a single file review"""
    logger.info(f"Reviewing file: {file.path}")
    
    # Prepare the prompt with file content
    prompt = f"{initial_prompt}\n\nFILE TO REVIEW:\n{file.content}"
    
    # Get LLM review asynchronously
    review_text = await async_create_message(prompt, model)
    
    # Save individual review asynchronously
    review_dir = Path("tests/initial_reviews")
    review_dir.mkdir(parents=True, exist_ok=True)
    review_path = review_dir / f"review_{timestamp}_{file.path.replace('/', '_')}.txt"
    
    # Write file in a non-blocking way
    with open(review_path, 'w') as f:
        f.write(review_text)
    
    return {
        'path': file.path,
        'content': file.content,
        'language': file.language,
        'size': file.size,
        'review': review_text
    }

async def process_initial_reviews(files, model):
    """Stage 1: Process individual file reviews concurrently"""
    logger.info("Starting initial file reviews...")
    
    # Load initial review prompt
    with open(Path("app/prompts/initial_review.txt"), "r") as f:
        initial_prompt = f.read()
    
    # Generate timestamp for this review session
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Process all files concurrently with semaphore to control concurrency
    sem = asyncio.Semaphore(10)  # Limit concurrent API calls
    
    async def process_with_semaphore(file):
        async with sem:
            return await process_single_file(file, model, initial_prompt, timestamp)
    
    tasks = [process_with_semaphore(file) for file in files]
    file_reviews = await asyncio.gather(*tasks)
    
    return file_reviews

async def process_batch_reviews(file_reviews, model):
    """Stage 2: Process batch reviews (groups of 10) concurrently"""
    logger.info("Starting batch reviews...")
    
    # Load batch review prompt
    with open(Path("app/prompts/batch_review.txt"), "r") as f:
        batch_prompt = f.read()
    
    # Create batch reviews directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    review_dir = Path("tests/batch_reviews")
    review_dir.mkdir(parents=True, exist_ok=True)
    
    # Group files into batches of 10
    batch_size = 10
    batches = [file_reviews[i:i + batch_size] for i in range(0, len(file_reviews), batch_size)]
    
    async def process_batch(batch, index):
        # Prepare batch content
        batch_content = "\n\n".join([f"File: {review['path']}\n{review['content']}" for review in batch])
        prompt = f"{batch_prompt}\n\nBATCH TO REVIEW:\n{batch_content}"
        
        # Get LLM review asynchronously
        review_text = await async_create_message(prompt, model)
        
        # Save batch review
        review_path = review_dir / f"batch_review_{timestamp}_batch_{index}.txt"
        with open(review_path, 'w') as f:
            f.write(review_text)
        
        return review_text
    
    # Process all batches concurrently
    tasks = [process_batch(batch, i) for i, batch in enumerate(batches, 1)]
    batch_reviews = await asyncio.gather(*tasks)
    
    return batch_reviews

async def process_merged_review(batch_reviews, model):
    """Stage 3: Process merged batch review"""
    logger.info("Starting merged batch review...")
    
    # Load merged review prompt
    with open(Path("app/prompts/merged_batch_review.txt"), "r") as f:
        merged_prompt = f.read()
    
    # Create merged reviews directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    review_dir = Path("tests/merged_batch_reviews")
    review_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare merged content
    merged_content = "\n\n".join([f"Batch Review {i+1}:\n{review}" for i, review in enumerate(batch_reviews)])
    prompt = f"{merged_prompt}\n\nBATCH REVIEWS TO MERGE:\n{merged_content}"
    
    # Get LLM review asynchronously
    review_text = await async_create_message(prompt, model)
    
    # Save merged review
    review_path = review_dir / f"merged_review_{timestamp}.txt"
    with open(review_path, 'w') as f:
        f.write(review_text)
    
    return review_text

async def process_final_review(merged_review, model):
    """Stage 4: Process final review"""
    logger.info("Starting final review...")
    
    # Load final review prompt
    with open(Path("app/prompts/final_review.txt"), "r") as f:
        final_prompt = f.read()
    
    # Create final reviews directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    review_dir = Path("tests/final_reviews")
    review_dir.mkdir(parents=True, exist_ok=True)
    
    prompt = f"{final_prompt}\n\nMERGED REVIEW TO FINALIZE:\n{merged_review}"
    
    # Get LLM review asynchronously
    review_text = await async_create_message(prompt, model)
    
    # Save final review
    review_path = review_dir / f"final_review_{timestamp}.txt"
    with open(review_path, 'w') as f:
        f.write(review_text)
    
    return review_text

async def main():
    try:
        console.print("Starting code review process...", style="bold green")
        
        # Get GitHub URL from user
        repo_url = await get_github_url()
        console.print(f"Processing repository: {repo_url}", style="bold blue")
        
        # Initialize extractor
        extractor = CodeExtractor()
        
        # Extract from repository using stream_github_files
        console.print("Extracting files from repository...")
        files = list(extractor.stream_github_files(repo_url))
        
        # Initialize review
        review = Review.create(
            repo_id=1,  # Test ID
            file_reviews=[]
        )
        
        # Process through review stages
        model = "claude-3-haiku-20240307"  # Using specified model
        
        # Stage 1: Initial Reviews (concurrent)
        file_reviews = await process_initial_reviews(files, model)
        review.file_reviews = file_reviews
        console.print("Initial file reviews completed.", style="green")
        
        # Stage 2: Batch Reviews (concurrent)
        batch_reviews = await process_batch_reviews(file_reviews, model)
        review.batch_reviews = batch_reviews
        console.print("Batch reviews completed.", style="green")
        
        # Stage 3: Merged Batch Review
        merged_review = await process_merged_review(batch_reviews, model)
        review.merged_batch_review = merged_review
        console.print("Merged batch review completed.", style="green")
        
        # Stage 4: Final Review
        final_review = await process_final_review(merged_review, model)
        review.final_review = final_review
        console.print("Final review completed.", style="green")
        
        # Save the complete review
        review.save()
        console.print("Review saved successfully!", style="bold green")
        
    except Exception as e:
        logger.error(f"Error during review process: {str(e)}")
        console.print(f"Error: {str(e)}", style="bold red")
        raise

if __name__ == "__main__":
    asyncio.run(main())
