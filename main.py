import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import os
import yt_dlp
from pathlib import Path

class TikTokDownloader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TikTok 다운로더")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # 기본 다운로드 폴더 설정
        self.download_path = str(Path.home() / "Downloads" / "TikTok")
        os.makedirs(self.download_path, exist_ok=True)
        
        self.setup_ui()
        
    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # URL 입력 부분
        url_frame = ttk.LabelFrame(main_frame, text="TikTok URL 입력 (한 줄에 하나씩)", padding="5")
        url_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        # URL 입력 텍스트 박스
        self.url_text = tk.Text(url_frame, height=6, wrap=tk.WORD)
        url_scrollbar = ttk.Scrollbar(url_frame, orient="vertical", command=self.url_text.yview)
        self.url_text.configure(yscrollcommand=url_scrollbar.set)
        
        self.url_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        url_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        url_frame.rowconfigure(0, weight=1)
        
        # URL 개수 표시
        self.url_count_var = tk.StringVar(value="URL 개수: 0")
        url_count_label = ttk.Label(url_frame, textvariable=self.url_count_var)
        url_count_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # URL 텍스트 변경 이벤트 바인딩
        self.url_text.bind('<KeyRelease>', self.update_url_count)
        self.url_text.bind('<Button-1>', self.update_url_count)
        
        # 다운로드 폴더 선택
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="저장 폴더:").grid(row=0, column=0, sticky=tk.W)
        
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = ttk.Entry(folder_frame, textvariable=self.path_var, state="readonly")
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        ttk.Button(folder_frame, text="찾아보기", 
                  command=self.select_folder).grid(row=0, column=2)
        
        # 품질 선택
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(quality_frame, text="화질:").grid(row=0, column=0, sticky=tk.W)
        
        self.quality_var = tk.StringVar(value="best")
        quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, 
                                   values=["best", "worst", "720p", "480p", "360p"],
                                   state="readonly", width=10)
        quality_combo.grid(row=0, column=1, padx=(5, 0), sticky=tk.W)
        
        # 워터마크 제거 옵션
        self.remove_watermark = tk.BooleanVar(value=True)
        watermark_check = ttk.Checkbutton(quality_frame, text="워터마크 제거", 
                                        variable=self.remove_watermark)
        watermark_check.grid(row=0, column=2, padx=(20, 0))
        
        # 다운로드 버튼과 전체 진행률
        download_frame = ttk.Frame(main_frame)
        download_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        download_frame.columnconfigure(1, weight=1)
        
        self.download_btn = ttk.Button(download_frame, text="전체 다운로드", 
                                     command=self.start_batch_download)
        self.download_btn.grid(row=0, column=0, padx=(0, 10))
        
        # 전체 진행률 표시
        self.batch_progress_var = tk.StringVar(value="대기 중...")
        batch_progress_label = ttk.Label(download_frame, textvariable=self.batch_progress_var)
        batch_progress_label.grid(row=0, column=1, sticky=tk.W)
        
        # 일시정지/재개 및 중단 버튼
        self.pause_btn = ttk.Button(download_frame, text="일시정지", 
                                  command=self.toggle_pause, state="disabled")
        self.pause_btn.grid(row=0, column=2, padx=(5, 5))
        
        self.stop_btn = ttk.Button(download_frame, text="중단", 
                                 command=self.stop_download, state="disabled")
        self.stop_btn.grid(row=0, column=3)
        
        # 다운로드 상태 플래그
        self.is_downloading = False
        self.is_paused = False
        self.should_stop = False
        
        # 진행률 표시
        self.progress_var = tk.StringVar(value="대기 중...")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=4, column=0, columnspan=2, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 로그 영역
        log_frame = ttk.LabelFrame(main_frame, text="로그", padding="5")
        log_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # URL 입력창에 포커스
        self.url_text.focus()
        
    def update_url_count(self, event=None):
        """URL 개수 업데이트"""
        text = self.url_text.get("1.0", tk.END).strip()
        if text:
            urls = [url.strip() for url in text.split('\n') if url.strip()]
            valid_urls = [url for url in urls if self.is_valid_tiktok_url(url)]
            self.url_count_var.set(f"URL 개수: {len(urls)} (유효: {len(valid_urls)})")
        else:
            self.url_count_var.set("URL 개수: 0")
    
    def is_valid_tiktok_url(self, url):
        """TikTok URL 유효성 검사"""
        return url.startswith(('https://www.tiktok.com', 'https://tiktok.com', 'https://vm.tiktok.com'))
    
    def get_urls_from_text(self):
        """텍스트 박스에서 URL 목록 추출"""
        text = self.url_text.get("1.0", tk.END).strip()
        if not text:
            return []
        
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        valid_urls = [url for url in urls if self.is_valid_tiktok_url(url)]
        
        return valid_urls
    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.download_path = folder
            self.path_var.set(folder)
    
    def toggle_pause(self):
        """일시정지/재개 토글"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.config(text="재개")
            self.log_message("다운로드 일시정지됨")
        else:
            self.pause_btn.config(text="일시정지")
            self.log_message("다운로드 재개됨")
    
    def stop_download(self):
        """다운로드 중단"""
        self.should_stop = True
        self.log_message("다운로드 중단 요청됨...")
        
    def start_batch_download(self):
        """여러 URL 일괄 다운로드 시작"""
        urls = self.get_urls_from_text()
        
        if not urls:
            messagebox.showerror("오류", "유효한 TikTok URL을 입력해주세요.\n한 줄에 하나씩 입력하세요.")
            return
        
        # 상태 초기화
        self.is_downloading = True
        self.is_paused = False
        self.should_stop = False
        
        # UI 상태 변경
        self.download_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        
        # 진행률 바 설정
        self.progress_bar.config(mode='determinate', maximum=len(urls), value=0)
        self.batch_progress_var.set(f"0/{len(urls)} 완료")
        
        self.log_message(f"일괄 다운로드 시작: {len(urls)}개 URL")
        
        # 다운로드를 별도 스레드에서 실행
        download_thread = threading.Thread(target=self.batch_download, args=(urls,))
        download_thread.daemon = True
        download_thread.start()
            
    def batch_download(self, urls):
        """여러 URL 일괄 다운로드 실행"""
        completed = 0
        failed = 0
        
        for i, url in enumerate(urls):
            if self.should_stop:
                self.log_message("다운로드가 사용자에 의해 중단되었습니다.")
                break
            
            # 일시정지 처리
            while self.is_paused and not self.should_stop:
                time.sleep(0.1)
            
            if self.should_stop:
                break
            
            try:
                self.log_message(f"[{i+1}/{len(urls)}] 다운로드 시작: {url}")
                self.root.after(0, lambda: self.progress_var.set(f"[{i+1}/{len(urls)}] 다운로드 중..."))
                
                # 개별 비디오 다운로드
                success = self.download_single_video(url)
                
                if success:
                    completed += 1
                    self.log_message(f"[{i+1}/{len(urls)}] 완료!")
                else:
                    failed += 1
                    self.log_message(f"[{i+1}/{len(urls)}] 실패!")
                
                # 진행률 업데이트
                self.root.after(0, lambda c=completed, f=failed, t=len(urls): 
                               self.update_batch_progress(c, f, t))
                
                # 진행률 바 업데이트
                self.root.after(0, lambda v=i+1: self.progress_bar.config(value=v))
                
            except Exception as e:
                failed += 1
                error_msg = f"[{i+1}/{len(urls)}] 오류: {str(e)}"
                self.log_message(error_msg)
                self.root.after(0, lambda c=completed, f=failed, t=len(urls): 
                               self.update_batch_progress(c, f, t))
        
        # 완료 처리
        self.root.after(0, lambda: self.batch_download_finished(completed, failed, len(urls)))
    
    def download_single_video(self, url):
        """단일 비디오 다운로드"""
        try:
            # yt-dlp 옵션 설정
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'format': self.quality_var.get() if self.quality_var.get() != 'best' else 'best',
                'quiet': True,  # 로그 출력 최소화
            }
            
            # 워터마크 제거 옵션
            if self.remove_watermark.get():
                ydl_opts['format'] = 'best[ext=mp4]/best'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            return True
            
        except Exception as e:
            return False
    
    def update_batch_progress(self, completed, failed, total):
        """일괄 다운로드 진행률 업데이트"""
        self.batch_progress_var.set(f"{completed}/{total} 완료 (실패: {failed})")
        
    def batch_download_finished(self, completed, failed, total):
        """일괄 다운로드 완료 처리"""
        self.is_downloading = False
        
        # UI 상태 복원
        self.download_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="일시정지")
        self.stop_btn.config(state="disabled")
        
        self.progress_var.set("대기 중...")
        self.batch_progress_var.set(f"완료: {completed}/{total} (실패: {failed})")
        
        # 완료 메시지
        if failed == 0:
            message = f"모든 다운로드가 완료되었습니다!\n성공: {completed}/{total}"
            messagebox.showinfo("완료", message)
        else:
            message = f"다운로드가 완료되었습니다.\n성공: {completed}/{total}\n실패: {failed}/{total}"
            messagebox.showwarning("완료", message)
        
        self.log_message(f"일괄 다운로드 완료 - 성공: {completed}, 실패: {failed}")
    
    def start_download(self):
        """단일 다운로드 (기존 호환성 유지)"""
        urls = self.get_urls_from_text()
        if urls:
            self.start_batch_download()
        else:
            messagebox.showerror("오류", "유효한 TikTok URL을 입력해주세요.")
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    def log_message(self, message):
        """로그 메시지 추가"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def download_video(self, url):
        """기존 단일 다운로드 함수 (호환성 유지)"""
        return self.download_single_video(url)
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            self.root.after(0, lambda: self.progress_var.set(f"다운로드 중... {percent} ({speed})"))
        elif d['status'] == 'finished':
            self.root.after(0, lambda: self.progress_var.set("다운로드 완료!"))
            
    def download_finished(self):
        """다운로드 완료 후 UI 상태 복원"""
        self.download_btn.config(state="normal")
        self.progress_bar.stop()
        self.progress_var.set("대기 중...")
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = TikTokDownloader()
        app.run()
    except ImportError as e:
        print("필요한 라이브러리가 설치되지 않았습니다.")
        print("다음 명령어로 설치해주세요:")
        print("pip install yt-dlp")
        input("엔터를 눌러 종료...")