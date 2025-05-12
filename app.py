from flask import Flask, render_template, request, redirect, send_from_directory, flash
from PIL import Image
import os
import requests
from werkzeug.utils import secure_filename

port = int(os.environ.get("PORT", 8099))

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages
UPLOAD_FOLDER = 'static/output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        images = request.files.getlist('images')
        max_width = int(request.form['max_width'])
        max_height = int(request.form['max_height'])
        quality = int(request.form['quality'])
        to_webp = 'webp' in request.form
        wp_upload = 'wp_upload' in request.form
        wp_url = request.form.get('wp_url', '').rstrip('/')
        wp_user = request.form.get('wp_user', '')
        wp_pass = request.form.get('wp_pass', '')

        optimized_files = []

        for img_file in images:
            filename = secure_filename(img_file.filename)
            name, ext = os.path.splitext(filename)
            output_ext = ".webp" if to_webp else ".jpg"
            output_path = os.path.join(UPLOAD_FOLDER, name + output_ext)

            try:
                img = Image.open(img_file)
                img.thumbnail((max_width, max_height), Image.LANCZOS)

                if to_webp:
                    img.save(output_path, 'WEBP', quality=quality, optimize=True)
                else:
                    img = img.convert('RGB')  # Ensure compatibility
                    img.save(output_path, 'JPEG', quality=quality, optimize=True)

                optimized_files.append(output_path)
                flash(f"Optimized: {filename}", "success")

                if wp_upload:
                    with open(output_path, 'rb') as f:
                        headers = {
                            'Content-Disposition': f'attachment; filename={os.path.basename(output_path)}',
                            'Content-Type': 'image/webp' if to_webp else 'image/jpeg',
                        }
                        res = requests.post(
                            f"{wp_url}/wp-json/wp/v2/media",
                            headers=headers,
                            data=f,
                            auth=(wp_user, wp_pass)
                        )
                        if res.status_code == 201:
                            flash(f"Uploaded to WordPress: {filename}", "info")
                        else:
                            flash(f"Failed WP upload: {filename}. Response: {res.text}", "error")

            except Exception as e:
                flash(f"Error with {filename}: {e}", "error")

        return redirect('/')

    return render_template('index.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
