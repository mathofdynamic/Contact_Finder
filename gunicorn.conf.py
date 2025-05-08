workers = 2  # Adjust based on your CPU cores (2-4 x num_cores)
threads = 2  # Number of threads per worker
worker_class = 'gthread'  # Use threads
timeout = 300  # Increase timeout to 5 minutes
worker_tmp_dir = '/dev/shm'  # Use RAM for temporary files
max_requests = 1000  # Restart workers after this many requests
max_requests_jitter = 50  # Add randomness to restarts

# Debugging
reload = False  # Disable auto-reload in production
preload_app = True  # Load app before forking workers to save memory
