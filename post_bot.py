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

# logging.basicConfig(filemode="logs/post_bot.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger('post_bot')

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

    def login(self, is_personal: bool = True, is_business: bool = True):
        """
        Login the linkedin site
        """
        self.driver.get(self.linkedin_login_url)
        self.driver.maximize_window()
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

        if is_personal:
            self.post_articles_for_personal_account()

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
            print(e)
            count += 1
            if count == 5:
                return {"is_rejected": 1, "reason": "Dict convert is failed"}
            return self.validate_article_with_llm(article, count=count)

    def post_articles_for_personal_account(self):
        """
        Post the articles to the personal account
        """
        try:
            # WebDriverWait(self.driver, 5).until(
            #     EC.presence_of_element_located((By.ID, "ember32"))
            # )
            buttons_list = self.driver.find_element(By.TAG_NAME, "button")
            is_btn_found = False
            for button in buttons_list:
                if "Start a post, try writing with AI" in button.text:
                    is_btn_found = True
                    share_post_button = button
                    break
            if not is_btn_found:
                raise sc_ex.TimeoutException("Start a post, try writing with AI -- Button is missing")
        except sc_ex.TimeoutException:
            logger.error(traceback.format_exc())
            # logger.error(str(ex))
            return None

        article_list = self.session.query(Article).filter(
                            Article.is_personal == True
                        ).filter(
                            Article.is_rejected == False
                        ).filter(
                            Article.is_posted == False
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
                self.driver.execute_script("arguments[0].click();", share_post_button)
                blog_content = f"""{article.title}\n{article.content}""".split("\n")
                editor_div = self.driver.find_element(By.CSS_SELECTOR, '.ql-editor')
                editor_div_p = editor_div.find_element(By.TAG_NAME, 'p')
                # self.type_like_human(editor_div_p, blog_content, start=0.1, end=0.3)
                for content in blog_content:
                    time.sleep(round(random.uniform(0.6, 2.0), 1))
                    self.driver.execute_script("arguments[0].innerHTML += '<p>' + arguments[1] + '</p>';", editor_div, content)
                time.sleep(1)

                # ember576_btn = self.driver.find_element(By.ID, "ember576")
                # ember576_btn.click()
                post_button = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, "//button[span[text()='Post']]"))
                                )
                # post_button.click()
                self.driver.execute_script("arguments[0].click();", post_button)
                time.sleep(3)

                self.session.add(article)
                self.session.commit()
