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
    - In this project my chrome version is `Version 130.0.6723.58 (Official Build) (64-bit)` & downloaded the ChromeDriver from this [link](https://storage.googleapis.com/chrome-for-testing-public/130.0.6723.58/linux64/chromedriver-linux64.zip). *keep in mind download the correct version of driver based on your chrome version* and *Unzip the file and copy and past the driver in the `workspace` directory*


# .env
Before starting the application please make sure you have the following environment variables
```py
DATABASE_NAME=linkedin_post_bot.db

GEMINI_MODEL_NAME=gemini-1.5-flash
GOOGLE_API_KEY=<YOUR_API_KEY>


LINKEDIN_CLIENT_ID=<YOUR_CLIENT_ID>
LINKEDIN_CLIENT_SECRET=<YOUR_CLIENT_SECRET>
LINKEDIN_COMPANY_ID=<YOUR_COMPANY_ID>
LINKEDIN_USERNAME=<YOUR_USERNAME>
LINKEDIN_PASSWORD=<YOUR_PASSWORD>
LINKEDIN_LOGIN_URL=https://www.linkedin.com/login

DRIVER_EXE_PATH=chromedriver
```

# Local setup
### Step 1: Clone the project
```
git clone https://github.com/Antony-M1/linkedin_post_bot.git
```
```
cd linkedin_post_bot
```

### Step 2: Create environment and install dependencies
Assume a you have `linux` machine or you are using the `git bash` terminal
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
pip install --no-cache-dir -r requirements.txt
```

### Step 3: Run the project
```
streamlit run main.py
```

# Run standalone
To run the `PostBot` alone just run the following command
```
python post_bot.py
```
make sure the `cookies.json` file exists. if not run this command
```
python post_bot.py --for_cookies
```