from dotenv import load_dotenv
import streamlit as st
from models import Article, create_engine_session
from post_bot import PostBot
from components import (
    create_article_form,
    create_article_list,
    create_ai_suggestion,
    create_script_run
)


load_dotenv()

Session = create_engine_session()
db_session = Session()

st.title('LinkedIn Post Bot')

tab_article, tab_article_list, tab_ai, tab_run = st.tabs(["📝 Article", "🗃 List of Articles", "🤖Gemini AI", "🏃 Run"]) # noqa

with tab_article:
    create_article_form(Article, db_session)

with tab_article_list:
    create_article_list(Article, db_session, generator=tab_article_list)

with tab_ai:
    create_ai_suggestion(generator=tab_ai)

with tab_run:
    create_script_run(PostBot, generator=tab_run)