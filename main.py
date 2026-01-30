import sys
import os
import pathlib
import yt_dlp

def get_ffmpeg_path():
    """
    Get FFmpeg path. Try imageio-ffmpeg first, then fall back to system FFmpeg.
    Returns the path or None if not found.
    """
    # Try imageio-ffmpeg first (bundled)
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        print(f"[Info] Using bundled FFmpeg from: {ffmpeg_path}")
        return ffmpeg_path
    except ImportError:
        print("[Info] imageio-ffmpeg not installed, checking system FFmpeg...")
    except Exception as e:
        print(f"[Warning] Could not load imageio-ffmpeg: {e}")
    
    # Fall back to system FFmpeg
    system_ffmpeg = None
    try:
        import shutil
        system_ffmpeg = shutil.which('ffmpeg')
        if system_ffmpeg:
            print(f"[Info] Using system FFmpeg from: {system_ffmpeg}")
            return system_ffmpeg
    except Exception as e:
        print(f"[Warning] Error checking system FFmpeg: {e}")
    
    # No FFmpeg found
    print("\n[WARNING] FFmpeg is not detected!")
    print("Merging video and audio streams might fail.")
    print("Please install FFmpeg or run: pip install imageio-ffmpeg\n")
    return None

def progress_hook(d):
    """Progress hook to display download status."""
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%')
        s = d.get('_speed_str', 'N/A')
        e = d.get('_eta_str', 'N/A')
        sys.stdout.write(f"\r[Downloading] Progress: {p} | Speed: {s} | ETA: {e}")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        print("\n[Finished] Download complete. Processing/Merging...")

def validate_and_prepare_url(user_input):
    """
    Validate user input and prepare the URL.
    Returns a string URL or raises ValueError.
    """
    if not user_input or not isinstance(user_input, str):
        raise ValueError("Input cannot be empty")
    
    # Clean the input
    cleaned_input = user_input.strip().strip('"').strip("'")
    
    if not cleaned_input:
        raise ValueError("Input cannot be empty after cleaning")
    
    # Check if it's a local file
    if os.path.isfile(cleaned_input):
        print(f"\n[Info] Detected local file: {cleaned_input}")
        # Convert to file URI - required by yt-dlp
        abs_path = os.path.abspath(cleaned_input)
        file_uri = pathlib.Path(abs_path).as_uri()
        print(f"[Info] Converted to URI: {file_uri}")
        return str(file_uri)  # Return file:// URI as string
    else:
        # Assume it's a URL
        return str(cleaned_input)  # Ensure it's a string

def main():
    print("=== MPD to MP4 Downloader ===\n")
    
    # Get FFmpeg path (optional)
    ffmpeg_path = get_ffmpeg_path()
    
    # Get User Input
    try:
        user_input = input("Enter the .mpd URL or Local File Path: ")
        url = validate_and_prepare_url(user_input)
    except ValueError as e:
        print(f"[Error] {e}")
        return
    except Exception as e:
        print(f"[Error] Failed to process input: {e}")
        return
    
    # Verify URL is a string
    if not isinstance(url, str):
        print(f"[Error] URL must be a string, got {type(url)}")
        return
    
    print(f"[Info] Processing URL: {url[:100]}...")  # Show first 100 chars
    
    # Get output filename
    output_name = input("Enter the desired output filename (e.g., video.mp4): ").strip()
    if not output_name:
        output_name = "output.mp4"
        print(f"[Info] No filename provided. Defaulting to '{output_name}'")
    
    if not output_name.lower().endswith('.mp4'):
        output_name += ".mp4"
    
    # Post-processor hook to handle Windows file locking
    def postprocessor_hook(d):
        """Hook to handle post-processing events."""
        if d['status'] == 'finished':
            # Give Windows a moment to release file handles
            import time
            time.sleep(0.5)
    
    # Configure yt-dlp options
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',  # Download best video and audio
        'merge_output_format': 'mp4',          # Merge into mp4
        'outtmpl': output_name,                # Output filename template
        'progress_hooks': [progress_hook],     # Custom progress hook
        'postprocessor_hooks': [postprocessor_hook],  # Post-processor hook for file handling
        'quiet': True,                         # Suppress default output to use our hook
        'no_warnings': False,
        'enable_file_urls': True,              # Required to allow file:// URIs
        'verbose': False,                      # Disable verbose for cleaner output
    }
    
    # For local files, set the base URL to help resolve relative fragment paths
    if url.startswith('file://'):
        # Extract directory from file path for base URL
        local_path = url.replace('file:///', '').replace('file://', '')
        base_dir = os.path.dirname(local_path)
        base_url = pathlib.Path(base_dir).as_uri() + '/'
        print(f"[Info] Setting base URL for fragments: {base_url}")
        ydl_opts['http_headers'] = {'Referer': base_url}
    
    # Add FFmpeg location if available
    if ffmpeg_path:
        ydl_opts['ffmpeg_location'] = ffmpeg_path
    
    print(f"\n[Info] Starting download for: {output_name}...")
    
    # Use different methods for local files vs URLs
    is_local_file = url.startswith('file://')
    
    if is_local_file:
        # For local MPD files, use ffmpeg directly (more reliable)
        print("[Info] Using FFmpeg to process local MPD file...")
        
        if not ffmpeg_path:
            print("[Error] FFmpeg is required to process local MPD files!")
            return
        
        # Convert file:// URI back to local path
        local_path = url.replace('file:///', '').replace('file://', '')
        # Handle Windows paths
        if os.name == 'nt' and local_path.startswith('/'):
            local_path = local_path[1:]  # Remove leading slash on Windows
        
        # Get the directory containing the MPD file
        mpd_dir = os.path.dirname(os.path.abspath(local_path))
        mpd_filename = os.path.basename(local_path)
        
        # Get absolute path for output file
        output_abs = os.path.abspath(output_name)
        
        print(f"[Info] MPD directory: {mpd_dir}")
        print(f"[Info] MPD filename: {mpd_filename}")
        
        # Diagnostic: List files in the MPD directory
        print(f"\n[Diagnostic] Files in {mpd_dir}:")
        try:
            for item in os.listdir(mpd_dir)[:20]:  # Show first 20 items
                item_path = os.path.join(mpd_dir, item)
                if os.path.isdir(item_path):
                    print(f"  [DIR]  {item}/")
                else:
                    print(f"  [FILE] {item}")
        except Exception as e:
            print(f"  Error listing directory: {e}")
        
        # Check if MPD file exists and is readable
        mpd_full_path = os.path.join(mpd_dir, mpd_filename)
        if not os.path.exists(mpd_full_path):
            print(f"\n[Error] MPD file does not exist: {mpd_full_path}")
            return
        
        print(f"\n[Info] MPD file exists and is accessible")
        print(f"[Info] MPD file size: {os.path.getsize(mpd_full_path)} bytes")
        
        # Read and inspect MPD file to check for remote URLs
        print(f"\n[Info] Inspecting MPD file content...")
        try:
            with open(mpd_full_path, 'r', encoding='utf-8') as f:
                mpd_content = f.read()
            
            # Check if MPD contains HTTP/HTTPS URLs
            has_remote_urls = 'http://' in mpd_content or 'https://' in mpd_content
            
            if has_remote_urls:
                print("[Info] MPD file contains remote URLs (http/https)")
                print("[Info] This MPD references online content, not local files")
                print("[Info] Switching to yt-dlp to download from the remote source...")
                
                # Extract base URL from MPD if possible
                import re
                
                # Try to find BaseURL tag first
                base_url_match = re.search(r'<BaseURL[^>]*>(https?://[^<]+)</BaseURL>', mpd_content, re.IGNORECASE)
                if base_url_match:
                    remote_url = base_url_match.group(1).strip()
                    print(f"[Info] Found BaseURL in MPD: {remote_url}")
                else:
                    # Look for media URLs (ignore w3.org schema URLs)
                    # Try to find URLs in media/initialization/segment tags
                    media_patterns = [
                        r'media="(https?://[^"]+)"',
                        r'initialization="(https?://[^"]+)"',
                        r'sourceURL="(https?://[^"]+)"',
                        r'<SegmentURL[^>]*>(https?://[^<]+)</SegmentURL>',
                    ]
                    
                    remote_url = None
                    for pattern in media_patterns:
                        url_match = re.search(pattern, mpd_content, re.IGNORECASE)
                        if url_match:
                            potential_url = url_match.group(1).strip()
                            # Skip w3.org URLs (XML schemas)
                            if 'w3.org' not in potential_url:
                                remote_url = potential_url
                                print(f"[Info] Found media URL in MPD: {remote_url}")
                                break
                    
                    if not remote_url:
                        print("[Warning] Could not extract a valid media URL from MPD")
                        print("[Info] The MPD might use relative paths with a remote base")
                        print("[Tip] Please provide the original URL where you downloaded this MPD from")
                        return
                
                # Use yt-dlp for remote content
                print(f"\n[Info] Using yt-dlp to download from remote source...")
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([remote_url])
                    print(f"\n[Success] Successfully saved as '{output_name}'")
                except Exception as e:
                    print(f"\n[Error] yt-dlp failed: {e}")
                    import traceback
                    traceback.print_exc()
                return
            else:
                print("[Info] MPD file contains only local/relative paths")
                print("[Warning] But the fragment files don't seem to exist!")
                print("[Tip] Make sure all fragment files referenced in the MPD are present")
        
        except Exception as e:
            print(f"[Warning] Could not read MPD file: {e}")
        
        try:
            import subprocess
            
            # Use ffmpeg to convert MPD to MP4
            # Run from the MPD directory so relative paths work
            cmd = [
                ffmpeg_path,
                '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',  # Allow file protocol
                '-allowed_extensions', 'ALL',  # Allow all file extensions (including .webp)
                '-i', mpd_filename,            # Input MPD file (relative to working dir)
                '-c', 'copy',                  # Copy streams without re-encoding (faster)
                '-y',                          # Overwrite output file
                output_abs                     # Output file (absolute path)
            ]
            
            print(f"[Info] Running FFmpeg from directory: {mpd_dir}")
            print(f"[Debug] Command: {' '.join(cmd)}")
            
            # Run with real-time output from the MPD directory
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=mpd_dir  # Change working directory to MPD location
            )
            
            # Print output in real-time
            print("\n--- FFmpeg Output ---")
            for line in process.stdout:
                print(line.rstrip())
            
            process.wait()
            print("--- End FFmpeg Output ---\n")
            
            if process.returncode == 0:
                print(f"[Success] Successfully saved as '{output_name}'")
            else:
                print(f"[Error] FFmpeg failed with return code {process.returncode}")
                print("[Tip] The MPD file might reference fragments that don't exist locally,")
                print("      or the file paths in the manifest might be incorrect.")
        
        except Exception as e:
            print(f"\n[Error] Failed to process with FFmpeg: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        # For remote URLs, use yt-dlp
        print("[Info] Using yt-dlp to download from URL...")
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Ensure we're passing a list of strings
                ydl.download([str(url)])
            print(f"\n[Success] Successfully saved as '{output_name}'")
        
        except yt_dlp.utils.DownloadError as e:
            print(f"\n[Error] Download failed: {e}")
        except Exception as e:
            print(f"\n[Error] An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()  # Print full traceback for debugging

if __name__ == "__main__":
    main()
