from flask import Flask, render_template, request
from prompt_mutator import mutate_prompt_variants, highlight_changes
from openai import OpenAI
from markupsafe import Markup
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY is not set.")

client = OpenAI(api_key=api_key)
app = Flask(__name__)

level_map = {
    "0": "minor",
    "1": "moderate",
    "2": "dramatic",
    "3": "random"
}

def generate_image(prompt_text):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    user_prompt = ""
    highlighted_list = []
    mutated_variants = []
    image_url = None
    selected = None
    level_display = None

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == "mutate":
            user_prompt = request.form.get('prompt')
            slider_value = request.form.get('level')
            level_display = ["Minor", "Moderate", "Dramatic", "Random"][int(slider_value)]
            mutated_variants = mutate_prompt_variants(user_prompt, level=level_map[slider_value])
            highlighted_list = [highlight_changes(user_prompt, m) for m in mutated_variants]

        elif form_type == "generate":
            selected = request.form.get('selected_prompt')
            user_prompt = request.form.get('original_prompt')
            level_display = request.form.get('level_display')

            # 🔁 Rebuild previous mutations for display
            mutated_variants = mutate_prompt_variants(user_prompt, level=level_map[[k for k,v in level_map.items() if v == level_display.lower()][0]])
            highlighted_list = [highlight_changes(user_prompt, m) for m in mutated_variants]

            image_url = generate_image(selected)

    return render_template("index.html",
                           original=user_prompt,
                           highlighted_list=highlighted_list,
                           mutated_variants=mutated_variants,
                           image_url=image_url,
                           selected=selected,
                           level_display=level_display)


if __name__ == '__main__':
    app.run(debug=True)
