from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import threading
import webbrowser

class NoCacheHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_no_cache_headers()
        SimpleHTTPRequestHandler.end_headers(self)

    def send_no_cache_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Expires', '0')

def get_live2d_model():
    live2d_models = []
    root_directory = Path('./')  # Use the current directory

    count = 1
    for sub_directory in root_directory.iterdir():
        if sub_directory.is_dir():
            model3_files = list(sub_directory.glob('**/*.model3.json'))

            if not model3_files:
                model_files = list(sub_directory.glob('**/*model.json'))
                for file in model_files:
                    sub_folder_name = file.parent.name
                    relative_path = file.relative_to(root_directory)  # Get the relative path
                    file_path = "../../" + "/".join(relative_path.parts)  # Prepend path parts with '../../'
                    model_info = {
                        "number": count,
                        "folder_name": sub_folder_name,
                        "file_path": file_path
                    }
                    live2d_models.append(model_info)
                    count += 1
            else:
                for file in model3_files:
                    sub_folder_name = file.parent.name
                    relative_path = file.relative_to(root_directory)  # Get the relative path
                    file_path = "../../" + "/".join(relative_path.parts)  # Prepend path parts with '../../'
                    model_info = {
                        "number": count,
                        "folder_name": sub_folder_name,
                        "file_path": file_path
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
    #webbrowser.open_new_tab(f"http://localhost:{PORT}/Gallery/index.html")

    print(f"Serving at http://localhost:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Start the server in a separate thread
    server_thread = threading.Thread(target=generate_json_and_start_server)
    server_thread.start()
