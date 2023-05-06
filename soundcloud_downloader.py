from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QPlainTextEdit, QFileDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QIcon
from PyQt6.QtCore import QObject, pyqtSignal
from mutagen.id3 import ID3, TIT2, TPE1
from mutagen.id3 import ID3NoHeaderError
from selenium.webdriver.chrome.service import Service
import time, os, youtube_dl, threading, sys

# https://soundcloud.com/user-353974670/likes

class ScraperThread(QObject, threading.Thread):
    # Create a signal for the worker thread
    thread_signal = pyqtSignal(str)

    def __init__(self, url, terminal_signal, selected_folder):
        super().__init__()
        self.url = url
        self.thread_signal.connect(terminal_signal)
        self.selected_folder = selected_folder

    def run(self):
        self.thread_signal.emit("Scraper worker thread initialized")
        scraper = SeleniumScraper(self.url, self.thread_signal, self.selected_folder)
        # Begin main scraper download sequence
        scraper.main()

class Pyside6App(QObject):
    # Define a signal that will be emitted when the terminal needs to be updated
    update_terminal_signal = pyqtSignal(str)
    # Set terminal as an attribute of this class
    terminal = None
    selected_folder = None

    def __init__(self):
        super().__init__()
        # Get the existing QApplication object or create a new one if it doesn't exist
        self.app = QApplication.instance() or QApplication([])
        self.exe_dir = getattr(sys, '_MEIPASS', os.getcwd())
        # Create the main window and store it in an instance variable
        self.main_window = self.define_pyside6_window()
        self.update_terminal_signal.connect(self.update_terminal)

    def update_terminal(self, message):
        # Check if the terminal widget has been defined
        if self.terminal is not None:
            # Append the message to the terminal
            self.terminal.appendPlainText(message)

    def define_pyside6_window(self):
        self.terminal = QPlainTextEdit()
        # Create the dialog window
        dialog = QDialog()
        dialog.setWindowTitle("Safeguard's SoundCloud Downloader")
        # Set window icon
        dialog.setWindowIcon(QIcon(os.path.join(self.exe_dir, 'window-icon.png')))
        # Add minimize and close buttons
        dialog.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # Disable window resizing
        dialog.setFixedSize(700, 300)

        # Set the dark theme palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(40, 40, 40))
        palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.black)
        palette.setColor(QPalette.Button, QColor(240, 120, 0))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        dialog.setPalette(palette)

        # Create the layout
        layout = QVBoxLayout(dialog)

        # Create the URL prompt text input
        url_input = QLineEdit()
        url_input.setPlaceholderText("https://soundcloud.com/user-353974670/likes")
        url_input.setStyleSheet("color: white; background-color: black;")
        url_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #555555; 
                border-radius: 8px; 
                padding: 6px;
                background-color: #404040;
                color: white;
            }
        """)

        # Create the "Download" button and connect it to a function
        def download_url():
            url = url_input.text().strip().lower()
            self.update_terminal(f"Downloading URL: {url}")
            # Invalid SoundCloud URL
            if not url.startswith("https://soundcloud.com/"):
                self.update_terminal("Error: Invalid SoundCloud URL")
            else:
                # Create a ScraperThread and pass the Pyside6App signal
                scraper_thread = ScraperThread(url, self.update_terminal_signal, self.selected_folder)
                # Start the ScraperThread
                scraper_thread.start()            

        download_button = QPushButton("Download", dialog)
        download_button.setStyleSheet("""
            QPushButton {
                background-color: #cb7600;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #dc8000;
            }
        """)
        download_button.clicked.connect(download_url)

        # Create the "Folder" button and connect it to a function
        def open_folder():
            if not self.selected_folder:
                folder_path = os.path.abspath(os.path.join(self.exe_dir, "songs"))
            else:
                folder_path = self.selected_folder
            try:
                os.startfile(folder_path)
            except:
                self.update_terminal(f"'{folder_path}' Default 'songs' folder cannot be found, new download path specification required")

        folder_button = QPushButton("Open Folder", dialog)
        folder_button.setStyleSheet("""
            QPushButton {
                background-color: #3074d3;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #3e7ed6;
            }
        """)
        folder_button.clicked.connect(open_folder)

        def choose_folder():
            file_dialog = QFileDialog(dialog)
            file_dialog.setFileMode(QFileDialog.Directory)
            file_dialog.setOption(QFileDialog.ShowDirsOnly, True)
            if file_dialog.exec_():
                selected_folder = file_dialog.selectedFiles()[0]
                self.update_terminal(f"Download path: {selected_folder}")
                self.selected_folder = selected_folder

        choose_folder_button = QPushButton("Specify Path", dialog)
        choose_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #6a41af;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #7246bb;
            }
        """)
        choose_folder_button.clicked.connect(choose_folder)    

        # Create the terminal widget
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0f0f0f;
                color: white;
                font-family: Consolas, Courier, monospace;
                font-size: 12px;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px;
            }
        """ + """
            QScrollBar:vertical {
                border: none;
                background-color: #292829;
                width: 14px;
                margin: 14px 0 14px 0;
            }

            QScrollBar::handle:vertical {
                background-color: #3a393a;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical {
                border: none;
                background: none;
            }
            QScrollBar::sub-page:vertical {
                border: none;
                background: none;
            }
        """)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(download_button, 3)
        button_layout.addWidget(folder_button, 2)
        button_layout.addWidget(choose_folder_button, 1)
        # Add elements to the window
        layout.addWidget(url_input)
        layout.addLayout(button_layout)
        # Add the output terminal widget to the layout
        layout.addWidget(self.terminal)

        return dialog

    def run_pyside6_window(self):
        # Show the window and run the application
        self.main_window.exec()

class SeleniumScraper(QObject):
    output_signal = pyqtSignal(str)
    def __init__(self, url, thread_signal, selected_folder):
        super().__init__()
        self.url = url
        self.thread_signal = thread_signal
        self.output_signal.connect(self.thread_signal)
        self.selected_folder = selected_folder
        self.exe_dir = getattr(sys, '_MEIPASS', os.getcwd())
    
    def launch_browser(self, url):
        # Get the path to the chromedriver executable
        driver_path = os.path.join(self.exe_dir, 'chromedriver_win32', 'chromedriver.exe')
        # Initialize the Service object
        service = Service(executable_path=driver_path)
        # Launch Chrome browser
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(service=service, options=options)
        # Navigate to SoundCloud likes page
        driver.get(url)

        return driver

    def update_soup(self, driver):
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_button.click()
        self.output_signal.emit("Cookies accepted")
        time.sleep(1)

        # Auto-scroll to the bottom of the page to load all dynamically loaded elements
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # This sleep value will be dependent on internet speed of the user
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            self.output_signal.emit(f"Scrolled to position {new_height}")
            if new_height == last_height:
                break
            last_height = new_height
        time.sleep(1)

        # Retrieve page source
        html_source = driver.page_source
        # Parse page source with Beautiful Soup
        soup = BeautifulSoup(html_source, 'html.parser')

        return soup

    def extract_elements_in_liked(self, soup, driver):
        with driver:
            # Get the handle of the original window
            original_window = driver.current_window_handle
            # Links and metadata lists
            links = []
            metadata = []

            # Find all song elements
            song_elements = soup.find_all('li', {'class': 'soundList__item'})
            for song_element in song_elements:
                # Extract link for the element regardless of track or playlist nature
                link_element = song_element.find('a', {'class': 'soundTitle__title'})
                if link_element is not None:
                    link = 'https://soundcloud.com' + link_element.get('href')
                else:
                    link = "Unknown"
                    self.output_signal.emit("Warning: link unknown")

                playlist_div = song_element.find('div', {'class': 'sound playlist streamContext'})
                # Element is a track and duplicate detection negative
                if not playlist_div and link not in links:
                    self.output_signal.emit("Element is a track\nDuplicate detection positive")
                    # Extract title
                    title_element = song_element.select_one('.soundTitle__title')
                    if title_element is not None:
                        title = title_element.text.strip()
                    else:
                        title = "Unknown"
                        self.output_signal.emit("Warning: title unknown")
                    # Extract artist
                    artist_element = song_element.find('a', {'class': 'soundTitle__username'})
                    if artist_element is not None:
                        artist = artist_element.text.strip()
                    else:
                        artist = "Unknown"
                        self.output_signal.emit("Warning: artist unknown")

                    scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                    self.output_signal.emit(scraped_data)
                    # Append link and metadata of track to be downloaded
                    links.append(link)
                    metadata.append((title, artist))
                # Element is a playlist
                else:
                    self.output_signal.emit("Element is a playlist")
                    # Open new tab
                    driver.execute_script("window.open('');")
                    # switch to new tab
                    driver.switch_to.window(driver.window_handles[1])
                    # Load playlist URL
                    driver.get(link)
                    # scroll down to load all songs
                    while True:
                        # scroll to bottom of page
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        # wait for page to load
                        time.sleep(1)
                        # check if end of page is reached
                        end_of_page = driver.execute_script("return window.innerHeight + window.pageYOffset >= document.body.scrollHeight;")
                        if end_of_page:
                            break
                    # Scrape song information in new tab
                    new_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    new_song_elements = new_soup.find_all('li', {'class': 'trackList__item'})
                    # Extract song information from playlist page
                    for new_song_element in new_song_elements:
                        # Extract link for the playlist element
                        link_element = new_song_element.find('a', {'class': 'trackItem__trackTitle'})
                        if link_element is not None:
                            link = 'https://soundcloud.com' + link_element.get('href')
                        else:
                            link = "Unknown"
                            self.output_signal.emit("Warning: link unknown")
                        # Duplicate detection negative
                        if link.split('?in=')[0] not in links:
                            # Extract title
                            title_element = new_song_element.select_one('.trackItem__trackTitle')
                            if title_element is not None:
                                title = title_element.text.strip()
                            else:
                                title = "Unknown"
                                self.output_signal.emit("Warning: title unknown")
                            # Extract artist from the soundTitle__titleContainer element
                            artist_element = soup.select_one('.soundTitle__username > span:nth-of-type(1)')
                            if artist_element is not None:
                                artist = artist_element.text.strip()
                            else:
                                artist = "Unknown"
                                self.output_signal.emit("Warning: artist unknown")
                            # All scraped data out
                            scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                            self.output_signal.emit(scraped_data)

                            # Append link and metadata of track to be downloaded
                            links.append(link)
                            metadata.append((title, artist))
                        else:
                            # Duplicate detection positive
                            self.output_signal.emit(f"{title} detected as a duplicate element. Skipping...\n")
                             

                # Close new tab
                if driver.current_window_handle != original_window:
                    driver.close()
                    # Switch back to original tab if still open
                    if original_window in driver.window_handles:
                        driver.switch_to.window(original_window)
                # Switch back to original tab
                if not driver.window_handles[0]:
                    driver.switch_to.window(driver.window_handles[0])

        return links, metadata          

    def extract_elements_in_playlist(self, soup, driver):
        with driver:
            # Links and metadata lists
            links = []
            metadata = []

            # Find all song elements
            song_elements = soup.find_all('li', {'class': 'trackList__item'})
            for song_element in song_elements:
                # Extract link for the playlist element
                link_element = song_element.find('a', {'class': 'trackItem__trackTitle'})
                if link_element is not None:
                    link = 'https://soundcloud.com' + link_element.get('href').split('?in=')[0]
                else:
                    link = "Unknown"
                    self.output_signal.emit("Warning: link unkown")
                # Duplicate detection negative
                if link not in links:
                    # Extract title
                    title_element = song_element.select_one('.trackItem__trackTitle')
                    if title_element is not None:
                        title = title_element.text.strip()
                    else:
                        title = "Unknown"
                        self.output_signal.emit("Warning: title unkown")
                    # Extract artist from the soundTitle__titleContainer element
                    artist_element = song_element.select_one('.trackItem__username')
                    if artist_element is not None:
                        artist = artist_element.text.strip()
                    else:
                        artist_element = song_element.select_one('.soundTitle__username > span:nth-of-type(1)')
                        if artist_element is not None:
                            artist = artist_element.text.strip()
                        else:
                            artist = "Unknown"
                            self.output_signal.emit("Warning: artist unkown")
                    # All scraped data out
                    scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                    self.output_signal.emit(scraped_data)

                    # Append link and metadata of track to be downloaded
                    links.append(link)
                    metadata.append((title, artist))
                else:
                    # Duplicate detection positive
                    self.output_signal.emit(f"{link} detected as a duplicate element. Skipping...\n")

        return links, metadata    

    # Write data to files
    def write_to_links_file(links):
        with open('links.txt', 'w') as l:
            for link in links:
                l.write(link + '\n')

    # Download the .mp3 files from links list
    def download_file_from_link(self, links, metadata, selected_folder):
        # Set the path to the ffmpeg executable file
        ffmpeg_path = os.path.join(self.exe_dir, 'ffmpeg-2023-04-30-git-e7c690a046-essentials_build', 'bin', 'ffmpeg.exe')
        if selected_folder is not None:
            download_path = selected_folder
        else:
            download_path = os.path.join(self.exe_dir, 'songs')
        if not os.path.exists(download_path):            
            # Create folder to store songs
            os.makedirs(download_path)
        
        # youtube-dl options
        ydl_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }],
            'ffmpeg_location': ffmpeg_path
        }

        # Initialize YoutubeDL with the options
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            for link, (title, artist) in zip(reversed(links), reversed(metadata)):
                # Replace characters that are not allowed in filenames
                title = title.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', "'").replace('<', '-').replace('>', '-').replace('|', '-')
                
                # Debugging statement: print the link, title, and artist to make sure they are correct
                print(f"Downloading {title} by {artist} from {link}")
                
                # Download song
                try:
                    result = ydl.extract_info(link, download=True)
                    downloaded_file = ydl.prepare_filename(result)
                    self.output_signal.emit(f"{downloaded_file} downloaded successfully!")
                except Exception as e:
                    self.output_signal.emit(f"Error downloading {title} by {artist}: {e}")
                    continue                          
                # Set metadata
                mp3_file = downloaded_file            
                # Load the ID3 tag information from the file
                try:
                    audio = ID3(mp3_file)
                except ID3NoHeaderError:
                    # If there is no existing ID3 tag, create a new one
                    audio = ID3()

                # Set the title and artist tags
                audio['TIT2'] = TIT2(encoding=3, text=title)
                audio['TPE1'] = TPE1(encoding=3, text=artist)               
                # Save the changes to the file
                audio.save(mp3_file)

                self.output_signal.emit(f"Metadata for {title} updated successfully!")

    def main(self):
        # Launch Selenium browser and load the url passed
        driver = SeleniumScraper.launch_browser(self, self.url)
        # Print to terminal using emit
        self.output_signal.emit("Chrome Driver instance loaded")
        # Update the soup HTML parser
        soup = SeleniumScraper.update_soup(self, driver)
        self.output_signal.emit("Soup has been updated")
        # Logic for link nature
        if self.url.endswith("/likes"):
            # Scrape elements from updated soup HTML parser
            links, metadata = SeleniumScraper.extract_elements_in_liked(self, soup, driver)
        elif "/sets" in self.url:
            # Scrape elements from updated soup HTML parser
            links, metadata = SeleniumScraper.extract_elements_in_playlist(self, soup, driver)
        self.output_signal.emit("Elements have been extracted")
        # Add link to links.txt
        SeleniumScraper.write_to_links_file(links)
        self.output_signal.emit("Links have been written to links.txt in cwd, for whatever reason")
        # Download songs and add metadata
        SeleniumScraper.download_file_from_link(self, links, metadata, self.selected_folder)
        self.output_signal.emit("youtube-dl download process completed")

if __name__ == "__main__":
    # Create the Pyside6App object
    pyside6_app = Pyside6App()
    pyside6_app.update_terminal("(つ≧▽≦)つ Welcome~~")
    pyside6_app.update_terminal("This tool works with liked tracks page, album playlist, and user-created playlist URLs")
    pyside6_app.update_terminal(".mp3 files are encoded at 320 kbps")
    # Run the PySide6 window
    pyside6_app.run_pyside6_window()