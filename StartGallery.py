from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import threading
import webbrowser
import os
import sys
import cv2
import numpy as np
import onnxruntime as rt
from huggingface_hub import hf_hub_download

#/\/\/\/\
# CAN BE RAN WITH -NOTAG to skip tags
#/\/\/\/\

# Download or define the model path
tagger_model_path = hf_hub_download(repo_id="skytnt/deepdanbooru_onnx", filename="deepdanbooru.onnx")

# Initialize the tagger_model variable
tagger_model = rt.InferenceSession(tagger_model_path, providers=['CPUExecutionProvider'])
tagger_model_meta = tagger_model.get_modelmeta().custom_metadata_map
tagger_tags = eval(tagger_model_meta['tags'])

class NoCacheHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_no_cache_headers()
        SimpleHTTPRequestHandler.end_headers(self)

    def send_no_cache_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')

def tagger_predict(image, score_threshold):
    s = 512
    h, w = image.shape[:-1]
    h, w = (s, int(s * w / h)) if h > w else (int(s * h / w), s)
    ph, pw = s - h, s - w
    resized_image = cv2.resize(image, (w, h), interpolation=cv2.INTER_AREA)
    resized_image = cv2.copyMakeBorder(resized_image, ph // 2, ph - ph // 2, pw // 2, pw - pw // 2, cv2.BORDER_REPLICATE)
    resized_image = resized_image.astype(np.float32) / 255
    resized_image = resized_image[np.newaxis, :]

    probs = tagger_model.run(None, {"input_1": resized_image})[0][0]
    probs = probs.astype(np.float32)

    res = []
    for prob, label in zip(probs.tolist(), tagger_tags):
        if prob < score_threshold:
            continue
        res.append(label)
    return res





def get_live2d_model():
    live2d_models = []
    root_directory = Path('./')  # Use the current directory
    count = 1
    script_directory = Path(__file__).resolve().parent  # Get the directory of the script

    for sub_directory in root_directory.iterdir():
        folder_rel_path = ''  # Set a default value
        if sub_directory.is_dir():
            # Look for '*.model3.json', '*model.json', and 'model.json'
            model_files = list(sub_directory.glob('**/*.model3.json')) + list(sub_directory.glob('**/*model.json'))
            if not model_files:
                model_files = list(sub_directory.glob('**/model.json'))

            if not model_files:
                print(f"No model found in folder: {sub_directory}")
                continue

            for file in model_files:
                sub_folder_name = file.parent.name
                relative_path = file 

                file_names = [f for f in os.listdir(relative_path.parent) if "thumbnail" in f.lower()]

                if file_names:
                    thumbnail_file = file_names[0]  # Use the first found file path
                    thumbnail_path = os.path.join(relative_path.parent, thumbnail_file)

                    img = cv2.imread(thumbnail_path)
                    if img is None:
                        print(f"Error: Could not read the image '{thumbnail_path}'.")
                        tags = ["NO_IMAGE"]  # Assign "NO_IMAGE" if the image cannot be read
                    else:
                        # Check if tags exist and are non-empty
                        output_file_path = 'Gallery/live2d_models.json'
                        existing_tags = {}
                        if Path(output_file_path).exists():
                            with open(output_file_path, 'r') as existing_file:
                                existing_data = json.load(existing_file)
                                existing_tags = {model['folder_name']: model['tags'] for model in existing_data}

                        if existing_tags.get(sub_folder_name) and existing_tags[sub_folder_name]:
                            print(f"Tags already exist for Model #{count} in folder: {sub_directory}/{sub_folder_name}. Skipping tagging.")
                            tags = existing_tags[sub_folder_name]
                        else:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            folder_rel_path = os.path.relpath(sub_directory, script_directory)
                            print(f"Creating Tags for Model #{count} in folder: {folder_rel_path}/{sub_folder_name}")
                            tags = tagger_predict(img, 0.5)
                            
                            # Remove brackets and quotes from tags
                            formatted_tags = ' '.join(tags)

                            # Save tags to folder_name.tags file
                            tags_file_path = os.path.join(relative_path.parent, f"{sub_folder_name}.tags")
                            with open(tags_file_path, 'w') as tags_file:
                                tags_file.write(formatted_tags)

                else:
                    print(f"No thumbnail found in directory: {relative_path.parent}")
                    tags = ["NO_IMAGE"]  # Assign "NO_IMAGE" if no thumbnail is found

                file_path = "../../" + "/".join(relative_path.parts)  # Prepend path parts with '../../'
                model_info = {
                    "number": count,
                    "folder_name": sub_folder_name,
                    "file_path": file_path,
                    "tags": tags
                }

                live2d_models.append(model_info)
                count += 1

    return live2d_models




def generate_json_and_start_server():

    live2d_models = get_live2d_model()

    # Define the path for the output JSON file inside the 'Gallery' folder
    output_file_path = 'Gallery/live2d_models.json'

    # Check if the file exists and write to it if it does
    if Path(output_file_path).exists():
        print(f"Warning: The file '{output_file_path}' already exists. It will be overwritten.")

    # Save the JSON data to the output file
    with open(output_file_path, 'w') as output_file:
        json.dump(live2d_models, output_file, indent=2)

    print(f"JSON data saved to {output_file_path}")

    # Start a simple HTTP server serving from the 'Gallery' folder with the custom handler
    PORT = 8000
    handler = NoCacheHTTPRequestHandler
    httpd = HTTPServer(('localhost', PORT), handler)
    
    # Navigate to the index page inside the 'Gallery' folder
    webbrowser.open_new_tab(f"http://localhost:{PORT}/Gallery/index.html")

    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=generate_json_and_start_server)
    server_thread.start()