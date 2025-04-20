import streamlit as st
import time
import numpy as np
from PIL import Image
import io
import threading
import queue

# Global queue for background processing
background_queue = queue.Queue()
# Flag to track if the background worker is running
worker_running = False

def start_background_worker():
    """Start the background worker thread if not already running"""
    global worker_running
    if not worker_running:
        worker_running = True
        threading.Thread(target=background_worker, daemon=True).start()

def background_worker():
    """Background worker that processes tasks from the queue"""
    global worker_running
    while True:
        try:
            # Get a task from the queue with a timeout
            task, args = background_queue.get(timeout=5)
            try:
                # Execute the task
                task(*args)
            except Exception as e:
                # Log errors but continue processing
                print(f"Error in background task: {e}")
            finally:
                # Mark the task as done
                background_queue.task_done()
        except queue.Empty:
            # If queue is empty for 5 seconds, exit the worker
            worker_running = False
            break

def clear_cache():
    """Clear the detection cache."""
    if "image_detection_cache" in st.session_state:
        st.session_state.image_detection_cache = {}
        if "cache_timestamps" in st.session_state:
            st.session_state.cache_timestamps = {}
        return True
    return False

def get_cache_size():
    """Get the current size of the detection cache."""
    if "image_detection_cache" in st.session_state:
        return len(st.session_state.image_detection_cache)
    return 0

def limit_cache_size(max_entries=50):
    """Limit the cache size by removing oldest entries."""
    if "image_detection_cache" not in st.session_state:
        st.session_state.image_detection_cache = {}
        
    cache = st.session_state.image_detection_cache
    if len(cache) <= max_entries:
        return
        
    # If we don't have timestamps, add them now
    if "cache_timestamps" not in st.session_state:
        st.session_state.cache_timestamps = {key: time.time() for key in cache.keys()}
    
    # Sort keys by timestamp (oldest first)
    sorted_keys = sorted(
        cache.keys(), 
        key=lambda k: st.session_state.cache_timestamps.get(k, float('inf'))
    )
    
    # Remove oldest entries until we're under the limit
    keys_to_remove = sorted_keys[:len(cache) - max_entries]
    for key in keys_to_remove:
        del cache[key]
        if key in st.session_state.cache_timestamps:
            del st.session_state.cache_timestamps[key]

def optimize_image_for_cache(image):
    """Optimize image for caching to reduce memory usage."""
    if image is None:
        return None
        
    # Convert to RGB if it's not already (removes alpha channel)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize large images to reduce memory footprint
    max_dim = 1200  # Maximum dimension
    width, height = image.size
    if width > max_dim or height > max_dim:
        if width > height:
            new_width = max_dim
            new_height = int(height * (max_dim / width))
        else:
            new_height = max_dim
            new_width = int(width * (max_dim / height))
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Convert to JPEG format in memory to reduce size
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)
    return Image.open(buffer)

def update_cache_entry(cache_key, results):
    """Update cache with optimized image."""
    if "image_detection_cache" not in st.session_state:
        st.session_state.image_detection_cache = {}
    
    if "cache_timestamps" not in st.session_state:
        st.session_state.cache_timestamps = {}
    
    # Create a copy of results to avoid modifying the original
    cached_results = results.copy()
    
    # Optimize the result image before caching
    if cached_results and "result_image" in cached_results and cached_results["result_image"] is not None:
        # Convert numpy array to PIL Image if needed
        if isinstance(cached_results["result_image"], np.ndarray):
            pil_image = Image.fromarray(cached_results["result_image"])
            cached_results["result_image"] = optimize_image_for_cache(pil_image)
        elif isinstance(cached_results["result_image"], Image.Image):
            cached_results["result_image"] = optimize_image_for_cache(cached_results["result_image"])
    
    # Update the cache
    st.session_state.image_detection_cache[cache_key] = cached_results
    st.session_state.cache_timestamps[cache_key] = time.time()

def preload_adjacent_images(images, current_idx, model_config, run_detection_func):
    """Preload adjacent images in the background to improve pagination performance."""
    if not images or len(images) <= 1:
        return
    
    # Start the background worker if not running
    start_background_worker()
    
    # Determine which images to preload (next and previous)
    indices_to_preload = []
    if current_idx + 1 < len(images):
        indices_to_preload.append(current_idx + 1)  # Next image
    if current_idx > 0:
        indices_to_preload.append(current_idx - 1)  # Previous image
    
    for idx in indices_to_preload:
        img = images[idx]
        from modules.detection_utils import get_cache_key
        cache_key = get_cache_key(img, model_config)
        
        # Only preload if not already in cache
        if cache_key not in st.session_state.image_detection_cache:
            # Add to background queue
            background_queue.put((preload_single_image, (img, model_config, run_detection_func, cache_key)))

def preload_single_image(img, model_config, run_detection_func, cache_key):
    """Process a single image in the background and add to cache."""
    try:
        # Skip if already in cache (double-check)
        if cache_key in st.session_state.image_detection_cache:
            return
            
        # Run detection without progress callback
        results = run_detection_func(img, model_config)
        
        # Update cache with the results
        update_cache_entry(cache_key, results)
    except Exception as e:
        # Silently handle errors in background processing
        print(f"Error preloading image: {e}")