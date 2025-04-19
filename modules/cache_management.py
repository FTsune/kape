import streamlit as st
import time
import numpy as np
from PIL import Image
import io

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
        return
        
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
    if isinstance(image, np.ndarray):
        # Convert numpy array to PIL Image
        image = Image.fromarray(image)
    
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
    
    # Optimize the result image before caching
    if results and "result_image" in results and results["result_image"] is not None:
        results["result_image"] = optimize_image_for_cache(results["result_image"])
    
    # Update the cache
    st.session_state.image_detection_cache[cache_key] = results
    st.session_state.cache_timestamps[cache_key] = time.time()

def preload_adjacent_images(uploaded_images, current_idx, current_model_config, get_cache_key_func):
    """Preload adjacent images to improve pagination performance."""
    if not uploaded_images or len(uploaded_images) <= 1:
        return
    
    # Define which indices to preload (next and previous)
    indices_to_preload = []
    if current_idx + 1 < len(uploaded_images):
        indices_to_preload.append(current_idx + 1)  # Next image
    if current_idx > 0:
        indices_to_preload.append(current_idx - 1)  # Previous image
    
    # Generate cache keys for adjacent images
    for idx in indices_to_preload:
        img = uploaded_images[idx]
        cache_key = get_cache_key_func(img, current_model_config)
        
        # Mark this key as "preloaded" in session state
        if "preloaded_cache_keys" not in st.session_state:
            st.session_state.preloaded_cache_keys = set()
        
        st.session_state.preloaded_cache_keys.add(cache_key)
