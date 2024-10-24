from streamlit.delta_generator import DeltaGenerator
from .custom_ex import ErrorNotDeltaGenerator


def create_script_run(PostBot, generator=None):
    """
    PostBot: is objec from the post_bot.py module
    """
    if isinstance(generator, DeltaGenerator):
        generator.subheader("Click the button below to post the article to your linked personal, business, or both accounts.")  # noqa
        submit = generator.button("Run Script", key="run_script", icon=":material/sprint:", type='primary')
        if submit:
            generator.info("Running script")
            post_bot = PostBot()
            post_bot.login()
    else:
        raise ErrorNotDeltaGenerator("Generator must be DeltaGenerator")
