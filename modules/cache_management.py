import streamlit as st
import time

def clear_cache():
    """Clear the detection cache."""
    if "image_detection_cache" in st.session_state:
        st.session_state.image_detection_cache = {}
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
