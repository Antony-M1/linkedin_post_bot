"""
README
This the Post Bot script
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import exceptions as sc_ex
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


class PostBot:
    def __init__(
                    self,
                    company_id: str = os.getenv('LINKEDIN_COMPANY_ID'),
                    username: str = os.getenv('LINKEDIN_USERNAME'),
                    password: str = os.getenv('LINKEDIN_PASSWORD'),
                    linkedin_login_url: str = os.getenv("LINKEDIN_LOGIN_URL", "https://www.linkedin.com/login"),
                ):
        self.company_id = company_id
        self.username = username
        self.password = password
        self.linkedin_login_url = linkedin_login_url
        self.business_url = "https://www.linkedin.com/company/{0}/admin/page-posts/published/".format(company_id)
        self.linkedin_feed_url = "https://www.linkedin.com/feed/"
        # Driver
        self.driver_exe_path = os.path.join(os.getcwd(), os.getenv('DRIVER_EXE_PATH', 'chromedriver'))
        self.service = Service(executable_path=self.driver_exe_path)
        self.driver = webdriver.Chrome(service=self.service)

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

    def get_share_post_button(self):
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

            time.sleep(round(random.uniform(2, 5), 1))

            with open("cookies.json", "w") as file:
                json.dump(self.driver.get_cookies(), file)

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
                                Article.is_posted == False # noqa
                            ).all()

        for article in article_list:
            llm_response = self.validate_article_with_llm(article)
            if llm_response.get('is_rejected'):
                article.is_rejected = 1
                article.reason = llm_response.get('reason')
            else:
                article.is_posted = 1

            if not article.is_rejected:
                # ember32_btn = self.driver.find_element(By.ID, "ember32")
                # ember32_btn.click()
                share_post_button = get_share_post_button()
                if not share_post_button:
                    continue
                self.driver.execute_script("arguments[0].click();", share_post_button)
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
                    for letter in content:
                        time.sleep(round(random.uniform(0.1, 0.5), 1))
                        self.driver.execute_script("arguments[0].innerHTML = '<p>' + arguments[1] + '</p>';", editor_div, letter) # noqa
                    self.driver.execute_script("arguments[0].innerHTML += '<p>' + arguments[1] + '</p>';", editor_div, "") # noqa
                time.sleep(1)

                post_button = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//button[span[text()='Post']]"))
                                )
                self.driver.execute_script("arguments[0].click();", post_button)
                time.sleep(3)

            self.session.add(article)
            self.session.commit()

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
        self.driver.get(self.business_url)
        time.sleep(round(random.uniform(3, 10), 1))
        article_list = self.session.query(Article).filter(
                            Article.is_business == True # noqa
                        ).filter(
                            Article.is_rejected == False # noqa
                        ).filter(
                            Article.is_posted == False # noqa
                        ).all()
        for article in article_list:
            llm_response = self.validate_article_with_llm(article)
            if llm_response.get('is_rejected'):
                article.is_rejected = 1
                article.reason = llm_response.get('reason')
            else:
                article.is_posted = 1

            if not article.is_rejected:
                share_post_button = get_share_post_button()
                if not share_post_button:
                    logger.error("Share button is not there")
                    return
                self.driver.execute_script("arguments[0].click();", share_post_button)
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
