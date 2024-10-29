"""
# PostBot

This script contains the main class, `PostBot`,
which can be used to automate personal and business blog posts.

## Usage

To run the script, use the following command:

```bash
python post_bot.py --for_cookies
```

- When run with the `--for_cookies` argument, the script will just used to lodin and get the cookies.
- When run without `--for_cookies`, the script will start in scheduler mode, running at regular intervals.
To stop the scheduler, press `Ctrl + C` in the terminal.

Note:
- Don't set the scheduler interval very low because before finish one scheduler it will be
  Trigger the another scheduler. that's the reason for the double page showing.
""" # noqa
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import exceptions as sc_ex
from apscheduler.schedulers.background import BackgroundScheduler
from selenium.webdriver.chrome.options import Options
import pyfiglet
import argparse
import time
import os
import random
import requests
import json
import traceback
from bs4 import BeautifulSoup
import google.generativeai as genai
from models import Article, create_engine_session
from logger_config import get_logger
from dotenv import load_dotenv
load_dotenv()


logger = get_logger("post_bot", "post_bot.log")
logger_schedule = get_logger("apscheduler", "schedule.log")

parser = argparse.ArgumentParser(description="Post bot Arguments")
parser.add_argument("--for_cookies", help="Run for cookies", action="store_true")
args = parser.parse_args()


class PostBot:
    def __init__(
                    self,
                    company_id: str = os.getenv('LINKEDIN_COMPANY_ID'),
                    username: str = os.getenv('LINKEDIN_USERNAME'),
                    password: str = os.getenv('LINKEDIN_PASSWORD'),
                    linkedin_login_url: str = os.getenv("LINKEDIN_LOGIN_URL", "https://www.linkedin.com/login"),
                    post_interval: int = 60,
                    is_headless: bool = False
                ):
        self.company_id = company_id
        self.username = username
        self.password = password
        self.linkedin_login_url = linkedin_login_url
        self.business_url = "https://www.linkedin.com/company/{0}/admin/page-posts/published/".format(company_id)
        self.linkedin_feed_url = "https://www.linkedin.com/feed/"
        self.post_interval = post_interval

        # Driver
        options = Options()
        if is_headless and os.path.exists("cookies.json"):
            options.add_argument("--headless")
        self.driver_exe_path = os.path.join(os.getcwd(), os.getenv('DRIVER_EXE_PATH', 'chromedriver'))
        self.service = Service(executable_path=self.driver_exe_path)
        self.driver = webdriver.Chrome(service=self.service, options=options)

        # Database
        Session = create_engine_session()
        self.session = Session()

        # policy
        policy_url = "https://www.linkedin.com/legal/professional-community-policies"
        response = requests.get(policy_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        self.policy_content = soup.get_text(separator='\n', strip=True)

    def type_like_human(self, element: WebElement, value: str, start: int = 0.5, end: int = 2, is_enter: bool = False):
        try:
            for i in value:
                time.sleep(round(random.uniform(start, end), 1))
                element.send_keys(i)
            if is_enter:
                element.send_keys(Keys.RETURN)
        except sc_ex.NoSuchWindowException as ex:
            logger.exception("type_like_human " + str(ex))

    def get_share_post_button(self, count: int = 0):
        """Returns the share button"""
        try:
            buttons_list = self.driver.find_elements(By.TAG_NAME, "button")
            is_btn_found = False
            for button in buttons_list:
                if button.text in ["Start a post, try writing with AI", "Start a post"]:
                    is_btn_found = True
                    self.driver.execute_script("arguments[0].click();", button)
                    return button
            if not is_btn_found:
                raise sc_ex.TimeoutException("Start a post, try writing with AI -- Button is missing")
        except sc_ex.TimeoutException:
            logger.error(traceback.format_exc())
            return
        except sc_ex.ElementClickInterceptedException:
            logger.error(traceback.format_exc())
            self.close_pop_up()
            return self.get_share_post_button()
        except Exception:
            if count == 4:
                return
            self.close_pop_up()
            count += 1
            return self.get_share_post_button(count=count)

    def login(self, is_personal: bool = True, is_business: bool = True):
        """
        Login the linkedin site
        """
        share_post_btn = None
        self.driver.get(self.linkedin_login_url)
        time.sleep(round(random.uniform(0.6, 2.0), 1))
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r") as file:
                cookies = json.load(file)
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                time.sleep(round(random.uniform(0.6, 2.0), 1))
                self.driver.get(self.linkedin_feed_url)
                time.sleep(3)
                share_post_btn = self.get_share_post_button()

        self.driver.maximize_window()

        if not share_post_btn:

            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_input = self.driver.find_element(By.ID, "username")
            self.type_like_human(username_input, self.username)

            password_input = self.driver.find_element(By.ID, "password")
            self.type_like_human(password_input, self.password)

            time.sleep(round(random.uniform(0.6, 2.0), 1))

            sign_in_button = self.driver.find_element(By.CSS_SELECTOR, ".btn__primary--large")
            # sign_in_button.click()
            self.driver.execute_script("arguments[0].click();", sign_in_button)

            time.sleep(60)  # 1 minutes for otp

            self.refresh_cookies()

        if not args.for_cookies:
            if is_personal:
                self.post_articles_for_personal_account()

            if is_business:
                self.post_articles_for_business_account()

    def get_llm_response(self, content: str):
        try:
            model_name = os.getenv("GEMINI_MODEL_NAME")
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(content)
            return response.text
        except ValueError as ex:
            logger.critical(str(ex))
            return json.dumps({"is_rejected": 1, "reason": "HARM CONTENT"})

    def validate_article_with_llm(self, article: Article, count: int = 1):

        prompt = """I want you to validate the content of this article's title and description.
        It should comply with LinkedIn's terms & conditions. The blog should not violate LinkedIn's policy.
        Detect harmful or hateful content and return the response in JSON format like this:
        `{{"is_rejected": 1, "reason": "The content contains human rights violation content"}}`
        Provide the response strictly in JSON format.

        ### Here is the article title and description:
        Title: {}

        Description: {}

        Note: For reference, I have attached the policy content below:
        ### Policy content:
        {}
        """.format(article.title, article.content, self.policy_content)

        response = self.get_llm_response(prompt)
        try:
            return json.loads(response.replace("```json\n", "").replace("\n```", ""))
        except Exception as e:
            logger.error(traceback.format_exc())
            print(e)
            count += 1
            if count == 5:
                return {"is_rejected": 1, "reason": "Dict convert is failed"}
            return self.validate_article_with_llm(article, count=count)

    def post_articles_for_personal_account(self):
        """
        Post the articles to the personal account
        """
        def get_share_post_button():
            try:
                buttons_list = self.driver.find_elements(By.TAG_NAME, "button")
                is_btn_found = False
                for button in buttons_list:
                    if button.text in ["Start a post, try writing with AI", "Start a post"]:
                        is_btn_found = True
                        return button
                if not is_btn_found:
                    raise sc_ex.TimeoutException("Start a post, try writing with AI -- Button is missing")
            except sc_ex.TimeoutException:
                logger.error(traceback.format_exc())
                return

        article_list = self.session.query(Article).filter(
                            Article.is_personal == True # noqa
                            ).filter(
                                Article.is_rejected == False # noqa
                            ).filter(
                                Article.is_posted_personal == False # noqa
                            ).all()
        time.sleep(3)
        self.driver.get(self.linkedin_feed_url)
        time.sleep(3)
        for article in article_list:
            llm_response = self.validate_article_with_llm(article)
            if llm_response.get('is_rejected'):
                article.is_rejected = 1
                article.reason = llm_response.get('reason')
            else:
                article.is_posted_personal = 1

            if not article.is_rejected:
                share_post_button = self.get_share_post_button()
                if not share_post_button:
                    continue
                # self.driver.execute_script("arguments[0].click();", share_post_button)
                blog_content = f"""{article.title}\n{article.content}""".split("\n")
                time.sleep(round(random.uniform(2, 3.0), 1))
                try:
                    editor_div = self.driver.find_element(By.CSS_SELECTOR, '.ql-editor')
                except sc_ex.NoSuchElementException:
                    logger.error(traceback.format_exc())
                    editor_div = self.driver.find_element(By.CLASS_NAME, 'ql-editor')
                editor_div.clear()
                for content in blog_content:
                    time.sleep(round(random.uniform(0.6, 2.0), 1))
                    self.driver.execute_script("arguments[0].innerHTML += '<p>' + arguments[1] + '</p>';", editor_div, content) # noqa
                time.sleep(1)

                post_button = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//button[span[text()='Post']]"))
                                )
                self.driver.execute_script("arguments[0].click();", post_button)
                time.sleep(3)

            self.session.add(article)
            self.session.commit()
            time.sleep(self.post_interval)
            self.refresh_cookies()

    def post_articles_for_business_account(self):
        def get_share_post_button():
            try:
                buttons_list = self.driver.find_elements(By.TAG_NAME, "button")
                is_btn_found = False
                for button in buttons_list:
                    if button.text in ["Start a post, try writing with AI", "Start a post"]:
                        is_btn_found = True
                        return button
                if not is_btn_found:
                    raise sc_ex.TimeoutException("Start a post-- Button is missing")
            except sc_ex.TimeoutException:
                logger.error(traceback.format_exc())
                return
        time.sleep(round(random.uniform(3, 10), 1))
        self.driver.get(self.business_url)  # Load the business Page
        time.sleep(round(random.uniform(3, 10), 1))
        article_list = self.session.query(Article).filter(
                            Article.is_business == True # noqa
                        ).filter(
                            Article.is_rejected == False # noqa
                        ).filter(
                            Article.is_posted_business == False # noqa
                        ).all()
        for article in article_list:
            llm_response = self.validate_article_with_llm(article)
            if llm_response.get('is_rejected'):
                article.is_rejected = 1
                article.reason = llm_response.get('reason')
            else:
                article.is_posted_business = 1

            if not article.is_rejected:
                share_post_button = self.get_share_post_button()
                if not share_post_button:
                    logger.error("Share button is not there")
                    continue
                # self.driver.execute_script("arguments[0].click();", share_post_button)
                blog_content = f"""{article.title}\n{article.content}""".split("\n")
                time.sleep(round(random.uniform(2, 3.0), 1))
                try:
                    editor_div = self.driver.find_element(By.CSS_SELECTOR, '.ql-editor')
                except sc_ex.NoSuchElementException:
                    logger.error(traceback.format_exc())
                    editor_div = self.driver.find_element(By.CLASS_NAME, 'ql-editor')
                editor_div.clear()
                for content in blog_content:
                    time.sleep(round(random.uniform(0.6, 2.0), 1))
                    self.driver.execute_script("arguments[0].innerHTML += '<p>' + arguments[1] + '</p>';", editor_div, content) # noqa
                time.sleep(1)

                post_button = WebDriverWait(self.driver, 5).until(
                                        EC.presence_of_element_located((By.XPATH, "//button[span[text()='Post']]"))
                                    )
                # post_button.click()
                self.driver.execute_script("arguments[0].click();", post_button)
                time.sleep(3)
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, 'button')
                    for button in buttons:
                        if button.text == 'Not now':
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            break
                except Exception as ex: # noqa
                    logger.critical(traceback.format_exc())
                    pass

            self.session.add(article)
            self.session.commit()
            time.sleep(self.post_interval)
            self.refresh_cookies()

    def refresh_cookies(self):
        """
        If cookies have an expiry time, retrieve fresh cookies periodically and store them securely.

        even if cookies have a long expiry, it’s a good idea to save fresh cookies every iteration or hour.
        This keeps the session valid and minimizes the risk of issues due to unexpected session changes.

        Overrides the `cookies.json` file every time.
        """
        with open("cookies.json", "w") as file:
            json.dump(self.driver.get_cookies(), file)

    def close_pop_up(self):
        """
        When attempting to access an element in an automation script,
        an unexpected pop-up may appear and interrupt the workflow.
        In such cases, the pop-up should be closed to proceed.
        """
        close_buttons = self.driver.find_elements(By.TAG_NAME, 'button')
        for button in close_buttons:
            try:
                if "dismiss" == button.get_attribute("aria-label").lower():
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(2)
            except Exception:
                logger.error("close_pop_up ", traceback.format_exc())
                continue


def print_linkedin() -> dict:
    text = pyfiglet.figlet_format("Post Bot", font="slant")
    print(f"\033[1;34;40m{text}\033[0m")


def schedule_post_bot():
    """
    Post Interval in seconds
    """
    post_interval = 120
    bot = PostBot(post_interval=post_interval, is_headless=True)
    bot.login()


def start_script():
    """
    README
    please configure the cron and scedule job details and time betwee the post

    ## Example for a scedulre
    - Daily at a specific time (e.g., 8:00 AM):
    ```py
    scheduler.add_job(scheduled_task, 'cron', hour=8, minute=0)
    ```
    - Every 15 minutes:
    ```py
    scheduler.add_job(scheduled_task, 'interval', minutes=15)
    ```
    - Once a week on Saturday at midnight:
    ```py
    scheduler.add_job(scheduled_task, 'cron', day_of_week='sat', hour=0, minute=0)
    ```
    """
    try:
        print_linkedin()
        scheduler = BackgroundScheduler()
        scheduler.add_job(schedule_post_bot, 'interval', hours=1)
        scheduler.start()
        print()
        print("Scheduler started...🚀🚀🚀")
        schedule_post_bot()
    except Exception:
        logger_schedule.critical("start_script " + traceback.format_exc())

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Script Stopped 🚫 · ⛔ · ✋🏻🛑⛔️ · ⛔ · ⚠️ · 🛑 · ✋")
        logger_schedule.error("stop_script " + traceback.format_exc())
        scheduler.shutdown()


def get_cookies():
    """
    This function is only used to run the login page and get the cookies after 2FA
    """
    bot = PostBot()
    bot.login()


if __name__ == '__main__':
    if not args.for_cookies:
        start_script()
    else:
        get_cookies()
