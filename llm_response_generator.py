# LLMResponseGenerator class to encapsulate prompt submission
class LLMResponseGenerator:
    def __init__(self, model_name="gemini-2.5-pro", config=None):
        self.model = get_multimodal_model(model_name, config)

    def submit_prompt(self,prompt):
        # prompt should be a list of messages
        return self.model.generate_content(prompt).text


import os

current_dir = os.path.dirname(os.path.abspath(__file__))
key_path = os.path.join(current_dir, "credentials", "key.json")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path


import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="statspeak-484706", location="us-central1")

# --- Configuration ---
generation_config = {
    "max_output_tokens": 8192,
    "temperature": 0.5,
    "top_p": 0.95,
}


# Function to build and return a GenerativeModel instance
def get_multimodal_model(model_name="gemini-2.5-pro", config=None):
    if config is None:
        config = generation_config
    return GenerativeModel(model_name, generation_config=config)
