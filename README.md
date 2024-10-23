# LinkedIn Post Bot

A script that automates posting articles to LinkedIn personal and business feeds using Python, Selenium, and SQLite for content management.

**Prerequisites:**
- [Python 3.10+](https://www.python.org/downloads/)
- [Selenium](https://pypi.org/project/selenium/#history)
- SQLite
- [ChromeDriver](https://sites.google.com/chromium.org/driver/downloads) (or another WebDriver)
    - This project is build on the `ChromeDriver` so the upcoming all the dependencies related to the ChromeDriver only.
    - Before downloading the ChromeDriver Go To The `About Chrome`, past this in chrome tap `chrome://settings/help`, It will take you to the about page take a note about the ChromeDriver Version. Better to use the latest stable version.
    - Go to the [chrome for testing](https://googlechromelabs.github.io/chrome-for-testing/) page and download the ChromeDriver.
    - In this project my chrome version is `Version 130.0.6723.58 (Official Build) (64-bit)` & downloaded the ChromeDriver from this [link](https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.58/linux64/chromedriver-linux64.zip). *keep in mind download the correct version of driver based on your chrome version*