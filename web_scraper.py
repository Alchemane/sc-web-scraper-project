from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QVBoxLayout, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
import sys, time, os, youtube_dl, shutil

# https://soundcloud.com/user-353974670/likes

class Pyside6App():
    def create_pyside6_window():
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
        url_label = QLabel("SoundCloud Liked URL:")
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
            if not url.startswith("https://soundcloud.com/") and not url.endswith("/likes"):
                print("Pyside6 Window: Error - Invalid SoundCloud URL")
            else:
                seleniumScraper = SeleniumScraper()
                seleniumScraper.main(url)

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

        # Add elements to the window
        layout.addWidget(url_label)
        layout.addWidget(url_input)
        layout.addWidget(download_button)

        return dialog

    def run_pyside6_window():
        # Create the application object
        dialog = QApplication(sys.argv)
        # Create the dialog window
        dialog = Pyside6App.create_pyside6_window()
        # Show the window and run the application
        dialog.exec()

class SeleniumScraper():
    def launch_browser(url):
        # Launch Chrome browser
        options = webdriver.ChromeOptions()
        options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(options=options)
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

    def extract_element(soup, driver):
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

                if link not in links:
                    playlist_div = song_element.find('div', {'class': 'sound playlist streamContext'})
                    # Element is a track
                    if not playlist_div:
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

                            # Extract link for the playlist element
                            link_element = new_song_element.find('a', {'class': 'trackItem__trackTitle'})
                            if link_element is not None:
                                link = 'https://soundcloud.com' + link_element.get('href')
                            else:
                                link = "Unknown"
                                print('Selenium Browser: Error - Link is unknown')

                            scraped_data = f'Title: {title}\nArtist: {artist}\nLink: {link}\n'
                            print('Selenium Browser: ' + scraped_data)
                            # Append link and metadata of track to be downloaded
                            links.append(link)
                            metadata.append((title, artist))
                            data.append(scraped_data)
                else:
                    # Duplicate detected, element has already been scraped
                    print(f'Selenium Browser: {link} has already been scraped. Skipping...\n')
                    continue

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
        # Delete songs folder if it already exists
        if os.path.exists('songs'):
            shutil.rmtree('songs')
        # Create folder to store songs
        os.makedirs('songs')

        ydl_opts = {
            'outtmpl': 'songs/%(title)s.%(ext)s',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }]
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            for i in range(len(links)):
                link = links[i]
                title, artist = metadata[i]
                # Replace characters that are not allowed in filenames
                title = title.replace('/', '-').replace('\\', '-').replace(':', '-').replace('*', '-').replace('?', '-').replace('"', "'").replace('<', '-').replace('>', '-').replace('|', '-')
                # Download song
                try:
                    ydl.download([link])
                    print(f"{title} by {artist} downloaded successfully!")
                except Exception as e:
                    print(f"Error downloading {title} by {artist}: {e}")

    def main(self, url):
        # Launch Selenium browser and load the url passed
        driver = SeleniumScraper.launch_browser(url)
        print('Script: driver is loaded')
        # Update the soup HTML parser
        soup = SeleniumScraper.update_soup(driver)
        print('Script: soup is updated')
        # Scrape elements from updated soup HTML parser
        links, metadata, data = SeleniumScraper.extract_element(soup, driver)
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
        time.sleep(5)

if __name__ == "__main__":
    Pyside6App.run_pyside6_window()