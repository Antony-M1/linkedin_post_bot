import streamlit as st
from streamlit.delta_generator import DeltaGenerator
import pandas as pd


def create_article_form(model, session):
    st.title("Article Management")

    with st.form(key='article_form', clear_on_submit=True):

        st.write("### Add a New Article")
        title = st.text_input('Article Title', '')
        content = st.text_area('Article Content', '')
        # is_posted = st.selectbox('Is Posted?', [0, 1])
        is_personal = st.checkbox('Is Personal')
        is_business = st.checkbox('Is Business')
        submit_button = st.form_submit_button(label='Submit Article')
        if submit_button:
            if title.strip() == '' or content.strip() == '':
                st.error('Both Title and Content fields are required.')
            if title and content:
                new_article = model(title=title, content=content, is_personal=is_personal, is_business=is_business)
                session.add(new_article)
                session.commit()
                st.success('Article added successfully!')
            else:
                st.error('Title and Content are required.')


def create_article_list(model, session, generator: DeltaGenerator):

    def handle_on_select(*args, **kwargs):
        try:
            index = st.session_state.articles['selection']['rows'][0]
            has_index = True
        except IndexError:
            has_index = False

        if has_index:
            data = df.iloc[index]
            generator.subheader(data.Title)
            generator.write(data.Content)
            post_article = generator.button(
                                "Post Article",
                                type="primary",
                                icon=":material/post_add:",
                                disabled=bool(data['Is Posted']) if data['Is Posted'] else bool(data['Is Posted'])
                            )
            if post_article:
                generator.success('Article Posted successfully!')

    articles = session.query(model).all()
    articles_dict = {
        'Article ID': [article.id for article in articles],
        "Title": [article.title for article in articles],
        "Content": [article.content for article in articles],
        "Is Posted Personal": [bool(article.is_posted_personal) for article in articles],
        "Is Posted Business": [bool(article.is_posted_business) for article in articles],
        "Is Personal": [bool(article.is_personal) for article in articles],
        "Is Business": [bool(article.is_business) for article in articles],
        "Is Rejected": [bool(article.is_rejected) for article in articles],
        "Reason": [article.reason for article in articles]
    }
    df = pd.DataFrame(articles_dict)
    df.set_index('Article ID', inplace=True)

    column_config = {
        '_index': st.column_config.Column('ID')
    }

    generator.dataframe(
        df,
        key='articles',
        on_select=handle_on_select,
        use_container_width=True,
        selection_mode="single-row",
        column_config=column_config
    )
