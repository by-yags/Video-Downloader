
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
import json
from urllib.parse import urlparse
import queue
import time

class VideoDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal Video Downloader")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Queue for thread-safe GUI updates
        self.message_queue = queue.Queue()
        self.download_active = False
        
        # Check if yt-dlp is available
        self.check_dependencies()
        
        self.setup_ui()
        self.check_messages()
    
    def check_dependencies(self):
        """Check if yt-dlp is installed"""
        try:
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            self.yt_dlp_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.yt_dlp_available = False
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Universal Video Downloader", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URL input section
        ttk.Label(main_frame, text="Website URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(main_frame, width=60)
        self.url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # URL examples
        examples_text = "Examples: YouTube video/playlist, TikTok profile/video, Instagram, Twitter, etc."
        ttk.Label(main_frame, text=examples_text, font=('Arial', 8), 
                 foreground='gray').grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Download destination section
        ttk.Label(main_frame, text="Download Folder:").grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=(15, 5))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.folder_entry.insert(0, os.path.expanduser("~/Downloads"))
        
        folder_button = ttk.Button(folder_frame, text="Browse", command=self.browse_folder)
        folder_button.grid(row=0, column=1, padx=(5, 0))
        
        # Options section
        options_frame = ttk.LabelFrame(main_frame, text="Download Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        options_frame.columnconfigure(1, weight=1)
        
        # Quality selection
        ttk.Label(options_frame, text="Video Quality:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, 
                                   values=["best", "worst", "720p", "480p", "360p"], 
                                   state="readonly", width=20)
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Audio only option
        self.audio_only_var = tk.BooleanVar()
        audio_check = ttk.Checkbutton(options_frame, text="Audio only (MP3)", 
                                    variable=self.audio_only_var)
        audio_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Playlist option
        self.playlist_var = tk.BooleanVar(value=True)
        playlist_check = ttk.Checkbutton(options_frame, text="Download entire playlist/profile", 
                                       variable=self.playlist_var)
        playlist_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        # Info button
        self.info_button = ttk.Button(button_frame, text="Get Video Info", 
                                    command=self.get_video_info)
        self.info_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Download button
        self.download_button = ttk.Button(button_frame, text="Download Videos", 
                                        command=self.start_download)
        self.download_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_button = ttk.Button(button_frame, text="Stop Download", 
                                    command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(20, 0))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready to download...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Download Log", padding="10")
        log_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Dependency warning
        if not self.yt_dlp_available:
            self.log_message("⚠️ WARNING: yt-dlp is not installed!")
            self.log_message("Please install it using: pip install yt-dlp")
            self.log_message("Or: pip install --upgrade yt-dlp")
            self.download_button.config(state=tk.DISABLED)
            self.info_button.config(state=tk.DISABLED)
    
    def browse_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(initialdir=self.folder_entry.get())
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def log_message(self, message):
        """Add message to log (thread-safe)"""
        self.message_queue.put(('log', message))
    
    def update_progress(self, message):
        """Update progress label (thread-safe)"""
        self.message_queue.put(('progress', message))
    
    def check_messages(self):
        """Check for messages from worker threads"""
        try:
            while True:
                msg_type, message = self.message_queue.get_nowait()
                
                if msg_type == 'log':
                    self.log_text.insert(tk.END, f"{message}\n")
                    self.log_text.see(tk.END)
                elif msg_type == 'progress':
                    self.progress_var.set(message)
                elif msg_type == 'download_complete':
                    self.download_complete()
                elif msg_type == 'download_error':
                    self.download_error(message)
                
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_messages)
    
    def get_video_info(self):
        """Get information about the video/playlist"""
        if not self.yt_dlp_available:
            messagebox.showerror("Error", "yt-dlp is not installed!")
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL!")
            return
        
        def info_worker():
            try:
                self.update_progress("Getting video information...")
                
                cmd = ['yt-dlp', '--dump-json', '--flat-playlist', url]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    self.log_message(f"Found {len(lines)} video(s)")
                    
                    for i, line in enumerate(lines[:5]):  # Show first 5
                        try:
                            info = json.loads(line)
                            title = info.get('title', 'Unknown Title')
                            duration = info.get('duration_string', 'Unknown Duration')
                            self.log_message(f"{i+1}. {title} ({duration})")
                        except json.JSONDecodeError:
                            continue
                    
                    if len(lines) > 5:
                        self.log_message(f"... and {len(lines) - 5} more videos")
                
                else:
                    self.log_message(f"Error getting info: {result.stderr}")
                
                self.update_progress("Ready to download...")
                
            except Exception as e:
                self.log_message(f"Error: {str(e)}")
                self.update_progress("Error occurred")
        
        threading.Thread(target=info_worker, daemon=True).start()
    
    def start_download(self):
        """Start the download process"""
        if not self.yt_dlp_available:
            messagebox.showerror("Error", "yt-dlp is not installed!")
            return
            
        url = self.url_entry.get().strip()
        folder = self.folder_entry.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a URL!")
            return
        
        if not folder:
            messagebox.showwarning("Warning", "Please select a download folder!")
            return
        
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create folder: {str(e)}")
                return
        
        self.download_active = True
        self.download_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        
        def download_worker():
            try:
                self.log_message(f"Starting download from: {url}")
                self.log_message(f"Download folder: {folder}")
                self.update_progress("Downloading...")
                
                # Build yt-dlp command
                cmd = ['yt-dlp']
                
                # Output template
                if self.playlist_var.get():
                    cmd.extend(['-o', os.path.join(folder, '%(uploader)s/%(title)s.%(ext)s')])
                else:
                    cmd.extend(['-o', os.path.join(folder, '%(title)s.%(ext)s')])
                    cmd.append('--no-playlist')
                
                # Quality settings
                if self.audio_only_var.get():
                    cmd.extend(['-x', '--audio-format', 'mp3'])
                else:
                    quality = self.quality_var.get()
                    if quality == "best":
                        cmd.extend(['-f', 'best[height<=1080]/best'])
                    elif quality == "worst":
                        cmd.extend(['-f', 'worst'])
                    else:
                        height = quality.replace('p', '')
                        cmd.extend(['-f', f'best[height<={height}]/best'])
                # Additional options
                cmd.extend([
                    '--embed-metadata',
                    '--write-description',
                    '--write-info-json',
                    '--ignore-errors',
                    '--continue',
                    '--no-overwrites'
                ])
                
                cmd.append(url)
                
                # Run yt-dlp
                self.process = subprocess.Popen(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.STDOUT, 
                    text=True,
                    universal_newlines=True
                )
                
                # Read output in real-time
                for line in iter(self.process.stdout.readline, ''):
                    if not self.download_active:
                        break
                    
                    line = line.strip()
                    if line:
                        self.log_message(line)
                        
                        # Update progress based on output
                        if '[download]' in line and '%' in line:
                            self.update_progress(f"Downloading... {line}")
                        elif 'Downloading' in line:
                            self.update_progress("Downloading video...")
                
                self.process.wait()
                
                if self.download_active:
                    if self.process.returncode == 0:
                        self.message_queue.put(('download_complete', None))
                    else:
                        self.message_queue.put(('download_error', f"Process exited with code {self.process.returncode}"))
                
            except Exception as e:
                if self.download_active:
                    self.message_queue.put(('download_error', str(e)))
        
        threading.Thread(target=download_worker, daemon=True).start()
    
    def stop_download(self):
        """Stop the current download"""
        self.download_active = False
        try:
            if hasattr(self, 'process') and self.process:
                self.process.terminate()
        except:
            pass
        
        self.download_complete()
        self.log_message("Download stopped by user")
    
    def download_complete(self):
        """Handle download completion"""
        self.download_active = False
        self.download_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.update_progress("Download completed!")
        self.log_message("✅ Download finished!")
    
    def download_error(self, error):
        """Handle download error"""
        self.download_active = False
        self.download_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.update_progress("Download failed!")
        self.log_message(f"❌ Error: {error}")

def main():
    root = tk.Tk()
    app = VideoDownloader(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()