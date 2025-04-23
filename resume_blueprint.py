from flask import Blueprint, request, jsonify, send_from_directory, render_template, session, redirect, url_for
import os
import PyPDF2

resume_bp = Blueprint('resume', __name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_user_folder():
    """Returns the upload folder for the logged-in user."""
    if 'username' not in session:
        return None
    user_folder = os.path.join(UPLOAD_FOLDER, session['username'])
    os.makedirs(user_folder, exist_ok=True)
    return user_folder
@resume_bp.route('/new_resume')
def new_resume():
    """Opens a blank format.html unless editing an existing resume."""
    if 'editing_filename' not in session:  
        session.pop('resume_text', None)  # Clear only when it's not an edit
    else:
        session.pop('editing_filename', None)  # Once editing starts, reset filename
    return render_template('format.html', resume_text=session.get('resume_text', ''))



@resume_bp.route('/save_resume', methods=['POST'])
def save_resume():
    """Saves the generated PDF in the user's folder."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_folder = get_user_folder()
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    file_path = os.path.join(user_folder, file.filename)
    file.save(file_path)

    return jsonify({'message': 'Resume saved successfully!', 'filename': file.filename})

@resume_bp.route('/saved_resumes')
def saved_resumes():
    """Lists saved resumes for the logged-in user."""
    if 'username' not in session:
        return redirect(url_for('login'))

    user_folder = get_user_folder()
    files = os.listdir(user_folder) if user_folder else []
    return render_template('saved_resumes.html', resumes=files)

@resume_bp.route('/preview/<filename>')
def preview_resume(filename):
    """Allows the logged-in user to preview their resume in the browser."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(user_folder, filename)  # Open in browser

@resume_bp.route('/download/<filename>')
def download_resume(filename):
    """Allows the logged-in user to download their own resume."""
    if 'username' not in session:
        return redirect(url_for('login'))

    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(user_folder, filename, as_attachment=True)

@resume_bp.route('/edit_resume/<filename>')
def edit_resume(filename):
    """Loads an existing resume into the editor for editing."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    text_content = []
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                extracted_text = page.extract_text() or ""  # Prevent NoneType error
                text_content.append(extracted_text)

        session['resume_text'] = "\n".join(text_content)  # Store extracted text
        session['editing_filename'] = filename  # Store file name for future saving

    except Exception as e:
        return jsonify({'error': f'Error reading PDF: {str(e)}'}), 500

    return redirect(url_for('resume.new_resume'))  # Redirect to format.html for editing


@resume_bp.route('/delete_resume/<filename>', methods=['POST'])
def delete_resume(filename):
    """Deletes a specific resume from the user's folder."""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 403

    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'message': 'Resume deleted successfully'})
    else:
        return jsonify({'error': 'File not found'}), 404
@resume_bp.route('/select_template', methods=['POST', 'GET'])
def select_template():
    if request.method == 'POST':
        data = request.get_json()
        session['template_data'] = data
        return redirect(url_for('resume.select_template'))

    data = session.get('template_data', {})
    return render_template("finaltemplatespagedesign.html", **data)
