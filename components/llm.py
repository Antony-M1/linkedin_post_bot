import os
import requests
from streamlit.delta_generator import DeltaGenerator
from .custom_ex import ErrorNotDeltaGenerator
import google.generativeai as genai
from bs4 import BeautifulSoup


def create_ai_suggestion(generator=None):

    def get_gemini_response(question):
        response = model.generate_content(question)
        return response.text

    if isinstance(generator, DeltaGenerator):
        model_name = os.getenv("GEMINI_MODEL_NAME")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(model_name)
        generator.subheader("AI Blog Post Content")
        user_query = generator.text_input("Ask your question")
        policy = generator.checkbox("Apply LinkedIn Policies")
        policy_url = "https://www.linkedin.com/legal/professional-community-policies"
        policy_content = ""
        if policy:
            try:
                response = requests.get(policy_url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                policy_content = soup.get_text(separator='\n', strip=True)
                generator.info(f"Policy Applied Here the url: {policy_url}")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching the page: {e}")
                return None
        submit = generator.button("Generate", icon=":material/robot:", type="primary")
        if user_query and submit:
            prompt = f"""Generate a blog post based on the provided content. Please ensure the tone is polite and positive,
            avoiding any negativity. Create uplifting content while considering the LinkedIn policies mentioned below.
            If the policy content is not available, feel free to disregard that section.
            The 'User Queries' section contains the user-provided content; please base your response on these queries.
            note if a user ask abusive or unlawful content restrict them, or say `this content against my policies can't provide information`
            take the policy content only for validation don't generate the content to user. if user ask unappropriate content. directly restrict
            them with short responses.
            
            Note: Provide the blog post content with the respective hash tags and emoji

            # User Queries
            {user_query}

            # LinkedIn Policy
            {policy_content}

            # Response
            The final response should be structured as follows:
            ### Title:
            ### Blog Post Content:
            """ # noqa

            response = get_gemini_response(prompt)
            generator.write(response)
    else:
        raise ErrorNotDeltaGenerator("Generator must be DeltaGenerator")
