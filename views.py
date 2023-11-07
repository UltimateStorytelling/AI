from flask import Flask, request, jsonify, render_template
import os
import time
import requests
import json
import base64
from PIL import Image
from io import BytesIO

app = Flask(__name__)

class Prodia:
    def __init__(self, api_key, base=None):
        self.base = base or "https://api.prodia.com/v1"
        self.headers = {
            "X-Prodia-Key": api_key
        }

    def generate(self, params):
        response = self._post(f"{self.base}/sdxl/generate", params)
        return response.json()

    def get_job(self, job_id):
        response = self._get(f"{self.base}/job/{job_id}")
        return response.json()

    def wait(self, job):
        job_result = job
        while job_result['status'] not in ['succeeded', 'failed']:
            time.sleep(0.25)
            job_result = self.get_job(job['job'])
        return job_result

    def list_models(self):
        response = self._get(f"{self.base}/sdxl/models")
        return response.json()

    def list_samplers(self):
        response = self._get(f"{self.base}/sdxl/samplers")
        return response.json()

    def _post(self, url, params):
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, data=json.dumps(params))
        if response.status_code != 200:
            raise Exception(f"Bad Prodia Response: {response.status_code}")
        return response

    def _get(self, url):
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Bad Prodia Response: {response.status_code}")
        return response

prodia_client = Prodia(api_key="")

@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        prompt = request.form['prompt']
        negative_prompt = request.form.get('negative_prompt')
        steps = int(request.form['steps'])
        width = int(request.form['width'])
        height = int(request.form['height'])
        seed = int(request.form['seed'])
        model = 'sd_xl_base_1.0.safetensors [be9edd61]'
        cfg_scale = 7.0
        sampler = 'DPM++ 2M Karras'

        result = prodia_client.generate({
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "model": model,
            "steps": steps,
            "sampler": sampler,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "seed": seed
        })

        job = prodia_client.wait(result)
        image_url = job["imageUrl"]

        return render_template('result.html', image_url=image_url)
    else:
        return render_template('text_input.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5556)

def image_to_base64(image_path):
    with Image.open(image_path) as image:
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue())
    return img_str.decode('utf-8')
