from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton, QHBoxLayout, QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PyQt6.QtCore import QObject, pyqtSignal
from mutagen.id3 import ID3, TIT2, TPE1
from mutagen.id3 import ID3NoHeaderError
import sys, time, os, youtube_dl, shutil, threading

# https://soundcloud.com/user-353974670/likes

class ScraperThread(QObject, threading.Thread):
    # Create a signal to emit when the scraping is complete
    output_signal = pyqtSignal(str)
    update_terminal_signal = pyqtSignal(str)

    def __init__(self, url, output_signal):
        super().__init__()
        self.url = url
        self.output_signal = output_signal

        # Connect the update_terminal_signal to the emit_update_terminal method
        self.update_terminal_signal.connect(self.emit_update_terminal)

    def run(self):
        output_signal = self.output_signal
        scraper = SeleniumScraper(self.url, output_signal)
        scraper.main(self.url, self.output_signal)

    def emit_update_terminal(self, message):
        self.output_signal.emit(message)

class Pyside6App(QObject):
    # Define a signal that will be emitted when the terminal needs to be updated
    update_terminal_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Get the existing QApplication object or create a new one if it doesn't exist
        self.app = QApplication.instance() or QApplication([])
        # Create the main window and store it in an instance variable
        self.main_window = self.define_pyside6_window()
        # Create a scraper thread object and store it in an instance variable
        self.scraper_thread = ScraperThread(None, None)
        # Connect the scraper thread's signal to the update_terminal slot
        self.update_terminal_signal.connect(self.update_terminal)

    def define_pyside6_window(self):
        # Create the dialog window
        dialog = QDialog()
        dialog.setWindowTitle("Safeguard's SoundCloud Liked Downloader")
        # Disable window resizing
        dialog.setFixedSize(dialog.sizeHint())

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

        # Create the URL prompt label and text input
        url_label = QLabel("SoundCloud URL:")
        url_label.setStyleSheet("color: white;")
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
            print(f"Pyside6 Window: Downloading URL: {url}")
            # Invalid SoundCloud URL
            if not url.startswith("https://soundcloud.com/"):
                print("Pyside6 Window: Error - Invalid SoundCloud URL")
            else:
                # Create a ScraperThread and connect its scraping_complete signal to the show_info method
                scraper_thread = ScraperThread(url, self.update_terminal_signal)
                # Connect the scraper_thread's update_terminal signal to a lambda function that appends the message to the terminal widget
                scraper_thread.update_terminal_signal.connect(lambda message: self.update_terminal_signal.emit(message))
                # Start the ScraperThread
                scraper_thread.start()               

        download_button = QPushButton("Download", dialog)
        download_button.setStyleSheet("""
            QPushButton {
                background-color: #cc7a0e;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #d98a1f;
            }
        """)
        download_button.clicked.connect(download_url)

        # Create the "Folder" button and connect it to a function
        def open_folder():
            import os
            folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "songs"))
            os.startfile(folder_path)

        folder_button = QPushButton("Folder", dialog)
        folder_button.setStyleSheet("""
            QPushButton {
                background-color: #1e90ff;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #4d94ff;
            }
        """)
        folder_button.clicked.connect(open_folder)

        # Create the "Info" button and connect it to a function
        def show_info():
            info_dialog = QDialog(dialog)
            info_dialog.setWindowTitle("Safeguard's SoundCloud Downloader Info")
            #info_dialog.setFixedSize(info_dialog.sizeHint())

            # Set the same dark theme palette as the main window
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(30, 30, 30))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(40, 40, 40))
            palette.setColor(QPalette.AlternateBase, QColor(50, 50, 50))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            info_dialog.setPalette(palette)

            layout = QVBoxLayout(info_dialog)
            label = QLabel("This tool is designed to scrape and download either a Liked Tracks or a Playlist page from SoundCloud. This tool utilizes the browser automation Selenium WebDriver in order to load dynamic elements and scrape the SoundCloud URL page. The tool opens a Chrome Driver to achieve this and parses the fully loaded HTML page using BeautifulSoup4. The liked page includes tracks and playlsit albums, so when encountered with a playlist, the tool opens a new Chrome Driver tab to scrape the playlist data. All songs are downloaded in the Songs folder in the project directory. A standard likes page URL will look like this: 'https://soundcloud.com/user-353974670/likes', whilst a playlist will look like this: https://soundcloud.com/user-353974670/sets/digicore-hyperpop. Ensure that the playlist entered is not private, or else it cannot be traversed by the Chrome Driver.")
            label.setWordWrap(True)
            layout.addWidget(label)

            info_dialog.exec()

        info_button = QPushButton("Info", dialog)
        info_button.setStyleSheet("""
            QPushButton {
                background-color: purple;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background-color: #663399;
            }
        """)
        info_button.clicked.connect(show_info)

        # Create the terminal widget
        terminal = QPlainTextEdit()
        terminal.setReadOnly(True)
        terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: black;
                color: white;
                font-family: 'Courier New', Courier, monospace;
                font-size: 12px;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 6px;
            }
        """)

        # Button layout
        button_layout = QHBoxLayout()
        button_layout.addWidget(download_button, 3)
        button_layout.addWidget(folder_button, 2)
        button_layout.addWidget(info_button, 1)
        # Add elements to the window
        layout.addWidget(url_label)
        layout.addWidget(url_input)
        layout.addLayout(button_layout)
        # Add the output terminal widget to the layout
        layout.addWidget(terminal)

        return dialog
    
    def update_terminal(self, output):
        self.terminal.appendPlainText(output)

    def run_pyside6_window(self):
        # Show the window and run the application
        self.main_window.exec()

class SeleniumScraper(QObject):
    output_signal = pyqtSignal(str)
    def __init__(self, url, output_signal):
        super().__init__()
        self.url = url
        self.output = output_signal

    def update_terminal(self, message):
        self.output_signal.emit(message)
    
    def launch_browser(url):
        # Get the path to the chromedriver executable
        driver_path = os.path.join(os.getcwd(), 'driver', 'chromedriver_win32', 'chromedriver')
        # Launch Chrome browser
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(options=options, executable_path=driver_path)
        # Navigate to SoundCloud likes page
        driver.get(url)

        return driver

    def update_soup(driver):
        # Wait for page to load
        wait = WebDriverWait(driver, 10)
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_button.click()
        print("Selenium Browser: Cookies accepted")
        time.sleep(1)

        # Auto-scroll to the bottom of the page to load all dynamically loaded elements
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # This sleep value will be dependent on internet speed of the user
            time.sleep(3)
            new_height = driver.execute_script("return document.body.scrollHeight")
            print(f"Selenium Browser: Scrolled to position {new_height}")
            if new_height == last_height:
                break
            last_height = new_height
        time.sleep(1)

        # Retrieve page source
        html_source = driver.page_source
        # Parse page source with Beautiful Soup
        soup = BeautifulSoup(html_source, 'html.parser')

        return soup

    def extract_elements_in_liked(soup, driver):
        with driver:
            # Get the handle of the original window
            original_window = driver.current_window_handle
            # Links and metadata lists
            links = []
            metadata = []
            data = []

            # Find all song elements
            song_elements = soup.find_all('li', {'class': 'soundList__item'})
            for song_element in song_elements:
                # Extract link for the element regardless of track or playlist nature
                link_element = song_element.find('a', {'class': 'soundTitle__title'})
                if link_element is not None:
                    link = 'https://soundcloud.com' + link_element.get('href')
                else:
                    link = "Unknown"
                    print('Selenium Browser: Error - Link is unknown')

                playlist_div = song_element.find('div', {'class': 'sound playlist streamContext'})
                # Element is a track and duplicate detection negative
                if not playlist_div and link not in links:
                    print('Selenium Browser: Element is a track')
                    # Extract title
                    title_element = song_element.select_one('.soundTitle__title')
                    if title_element is not None:
                        title = title_element.text.strip()
                    else:
                        title = "Unknown"
                        print('Selenium Browser: Error - Title is unknown')
                    # Extract artist
                    artist_element = song_element.find('a', {'class': 'soundTitle__username'})
                    if artist_element is not None:
                        artist = artist_element.text.strip()
                    else:
                        artist = "Unknown"
                        print('Selenium Browser: Error - Artist is unknown')

                    scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                    print('Selenium Browser: ' + scraped_data)
                    # Append link and metadata of track to be downloaded
                    links.append(link)
                    metadata.append((title, artist))
                    data.append(scraped_data)
                # Element is a playlist
                else:
                    print('Selenium Browser: Element is a playlist')
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
                            print('Selenium Browser: Error - Link is unknown')
                        # Duplicate detection negative
                        if link.split('?in=')[0] not in links:
                            print(link.split('?in=')[0])
                            # Extract title
                            title_element = new_song_element.select_one('.trackItem__trackTitle')
                            if title_element is not None:
                                title = title_element.text.strip()
                            else:
                                title = "Unknown"
                                print('Selenium Browser: Error - Title is unknown')
                            # Extract artist from the soundTitle__titleContainer element
                            artist_element = soup.select_one('.soundTitle__username > span:nth-of-type(1)')
                            if artist_element is not None:
                                artist = artist_element.text.strip()
                            else:
                                artist = "Unknown"
                                print('Selenium Browser: Error - Artist is unknown')
                            # All scraped data out
                            scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                            print('Selenium Browser: ' + scraped_data)

                            # Append link and metadata of track to be downloaded
                            links.append(link)
                            metadata.append((title, artist))
                            data.append(scraped_data)
                        else:
                            # Duplicate detection positive
                            print(f"Selenium Browser: {link} detected as a duplicate element. Skipping...\n")
                             

                # Close new tab
                if driver.current_window_handle != original_window:
                    driver.close()
                    # Switch back to original tab if still open
                    if original_window in driver.window_handles:
                        driver.switch_to.window(original_window)
                # Switch back to original tab
                if not driver.window_handles[0]:
                    driver.switch_to.window(driver.window_handles[0])
            print('extraction finished')

        return links, metadata, data          

    def extract_elements_in_playlist(soup, driver):
        with driver:
            # Links and metadata lists
            links = []
            metadata = []
            data = []

            # Find all song elements
            song_elements = soup.find_all('li', {'class': 'trackList__item'})
            for song_element in song_elements:
                # Extract link for the playlist element
                link_element = song_element.find('a', {'class': 'trackItem__trackTitle'})
                if link_element is not None:
                    link = 'https://soundcloud.com' + link_element.get('href').split('?in=')[0]
                else:
                    link = "Unknown"
                    print('Selenium Browser: Error - Link is unknown')
                # Duplicate detection negative
                if link not in links:
                    # Extract title
                    title_element = song_element.select_one('.trackItem__trackTitle')
                    if title_element is not None:
                        title = title_element.text.strip()
                    else:
                        title = "Unknown"
                        print('Selenium Browser: Error - Title is unknown')
                    # Extract artist from the soundTitle__titleContainer element
                    artist_element = song_element.select_one('.trackItem__username')
                    if artist_element is not None:
                        artist = artist_element.text.strip()
                    else:
                        try:
                            artist_element = soup.select_one('.soundTitle__username > span:nth-of-type(1)')
                            if artist_element is not None:
                                artist = artist_element.text.strip()
                        except:    
                            artist = "Unknown"
                            print('Selenium Browser: Error - Artist is unknown')
                    # All scraped data out
                    scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                    print('Selenium Browser: ' + scraped_data)

                    # Append link and metadata of track to be downloaded
                    links.append(link)
                    metadata.append((title, artist))
                    data.append(scraped_data)
                else:
                    # Duplicate detection positive
                    print(f"Selenium Browser: {link} detected as a duplicate element. Skipping...\n")

            print('extraction finished')

        return links, metadata, data    

    # Write data to files
    def write_to_links_file(links):
        with open('links.txt', 'w') as l:
            for link in links:
                l.write(link + '\n')

    def write_to_data_file(data):
        with open('data.txt', 'w') as d:
            for data_element in data:
                d.write(data_element + '\n')

    # Download the .mp3 files from links list
    def download_file_from_link(links, metadata):
        # Set the path to the ffmpeg executable file
        ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg-2023-04-30-git-e7c690a046-essentials_build', 'bin', 'ffmpeg.exe')
        
        # Delete songs folder if it already exists
        if os.path.exists('songs'):
            shutil.rmtree('songs')
            
        # Create folder to store songs
        os.makedirs('songs')
        
        # youtube-dl options
        ydl_opts = {
            'outtmpl': 'songs/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
            'ffmpeg_location': ffmpeg_path
        }
        
        # Initialize YoutubeDL with the options
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            for i in range(len(links)):
                link = links[i]
                title, artist = metadata[i]
                
                # Replace characters that are not allowed in filenames
                title = title.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', "'").replace('<', '-').replace('>', '-').replace('|', '-')

                # Download song
                try:
                    result = ydl.extract_info(link, download=True)
                    downloaded_file = ydl.prepare_filename(result)
                    print(f"{downloaded_file} downloaded successfully!")
                except Exception as e:
                    print(f"Error downloading {title} by {artist}: {e}")
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
                print(f"Metadata for {title} updated successfully!")

    def main(self, url, output_signal):
        self.output_signal.connect(self.output.emit)

        # Launch Selenium browser and load the url passed
        driver = SeleniumScraper.launch_browser(url)
        print('Script: driver is loaded')
        self.output_signal.emit("Driver is loaded!")
        # Update the soup HTML parser
        soup = SeleniumScraper.update_soup(driver)
        print('Script: soup is updated')
        # Logic for link nature
        if url.endswith("/likes"):
            # Scrape elements from updated soup HTML parser
            links, metadata, data = SeleniumScraper.extract_elements_in_liked(soup, driver)
        elif "/sets" in url:
            # Scrape elements from updated soup HTML parser
            links, metadata, data = SeleniumScraper.extract_elements_in_playlist(soup, driver)
        print('Script: elements are extracted')
        # Add link to links.txt
        SeleniumScraper.write_to_links_file(links)
        print('Script: links are written to links.txt')
        # Add data to data.txt
        SeleniumScraper.write_to_data_file(data)
        print('Script: data are written to data.txt')
        # Download songs and add metadata
        SeleniumScraper.download_file_from_link(links, metadata)
        print('Script: download of songs complete')
        self.output_signal.emit("Script: download of songs complete!")

if __name__ == "__main__":
    # Create the Pyside6App object
    pyside6_app = Pyside6App()
    # Run the PySide6 window
    pyside6_app.run_pyside6_window()