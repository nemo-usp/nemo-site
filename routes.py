from flask import render_template, request, jsonify, redirect, url_for, flash, abort, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, date # Import date as well
import yaml
import re
import slugify
import bleach # Used for sanitizing HTML output
import markdown
from models import db, bcrypt, User, Material
from flask_flatpages import FlatPages
from datetime import datetime

# Initialize Flask-FlatPages extension
pages = FlatPages()

# Function to register all routes with the Flask app instance
def register_routes(app):
    # Initialize FlatPages with the app context
    pages.init_app(app)

    # --- Public Routes ---

    ## Home Page
    @app.route('/')
    def index():
        # Get all pages marked as 'published'
        published_pages = [p for p in pages if p.meta.get('status') == 'published']
        # Sort pages by date, newest first, using current time as fallback
        sorted_pages = sorted(published_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
        # Get the 6 most recent news posts
        news_posts = [p for p in sorted_pages if p.path.startswith('news/')][:6]
        # Get the current "Problem of the Month" (first one found that isn't solved)
        problem_post = next((p for p in sorted_pages if p.path.startswith('months-problems/') and not p.meta.get('is_solved')), None)
        # Render the index template with the fetched posts
        return render_template('index.html', 
                               logado=current_user.is_authenticated, 
                               news_posts=news_posts, 
                               problem_post=problem_post,
                               title="NEMO Home") # Add title

    ## Login Page
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            # Find user by email
            user = User.query.filter_by(email=request.form['email']).first()
            # Check if user exists and password is correct
            if user and user.check_password(request.form['password']):
                # Log the user in with Flask-Login
                login_user(user, remember=True) # Remember session across browser closes
                return redirect(url_for('index'))
            else:
                # Show error message if login fails
                flash('Invalid credentials.', 'danger')
        # Render login page (handles GET requests and failed POST requests)
        return render_template('login.html', title="Login")

    ## Logout Action
    @app.route('/logout')
    @login_required # Protect this route: only logged-in users can logout
    def logout():
        # Log the user out
        logout_user()
        return redirect(url_for('index'))

    ## About Page
    @app.route('/about')
    def about(): 
        return render_template('about.html', 
                               logado=current_user.is_authenticated,
                               title="Sobre") # Add title

    ## Materials Page
    @app.route('/materials')
    def materials():
        # Get all materials from DB, ordered by position
        all_materials = Material.query.order_by(Material.position.asc()).all()

        return render_template(
            'materials.html', 
            logado=current_user.is_authenticated,
            materials=all_materials, # Pass the list to the template
            title="Materiais"
        )
    
    ## Manage Materials Page (Admin)
    @app.route('/manage-materials', methods=['GET', 'POST'])
    @login_required
    def manage_materials():
        # This handles the form for adding a NEW material
        if request.method == 'POST':
            # --- Get Form Data ---
            title = request.form.get('title')
            description = request.form.get('description')
            pdf_file = request.files.get('pdf_file')

            if not title or not pdf_file or pdf_file.filename == '':
                flash('Title and PDF file are required.', 'danger')
                return redirect(url_for('manage_materials'))

            # --- Save the PDF File ---
            if pdf_file and allowed_file(pdf_file.filename):
                filename = secure_filename(pdf_file.filename)
                # We save PDFs to a subfolder to keep uploads organized
                save_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs')
                os.makedirs(save_dir, exist_ok=True) # Create 'static/uploads/pdfs/' if it doesn't exist
                save_path = os.path.join(save_dir, filename)
                pdf_file.save(save_path)
                
                # Store the *relative* path for use in url_for()
                db_path = os.path.join('uploads/pdfs', filename).replace('\\', '/')

                # --- Get Max Position ---
                # Find the highest position number and add 1
                max_pos = db.session.query(db.func.max(Material.position)).scalar() or 0
                new_position = max_pos + 1
                
                # --- Create Database Entry ---
                new_material = Material(
                    title=title,
                    description=description,
                    pdf_path=db_path,
                    position=new_position
                )
                db.session.add(new_material)
                db.session.commit()
                flash('New material added successfully.', 'success')
            else:
                flash('Invalid file type. Only PDFs are allowed (for now).', 'danger')
                
            return redirect(url_for('manage_materials'))

        # --- Handle GET Request ---
        # Get all materials, sorted by their position, for display
        all_materials = Material.query.order_by(Material.position.asc()).all()
        return render_template(
            'manage-materials.html',
            materials=all_materials,
            logado=current_user.is_authenticated,
            title="Manage Materials"
        )

    ## Delete Material Action
    @app.route('/manage-materials/delete/<string:id>', methods=['POST'])
    @login_required
    def delete_material(id):
        material_to_delete = db.session.get(Material, id)
        if not material_to_delete:
            flash('Material not found.', 'danger')
            return redirect(url_for('manage_materials'))
        
        # (Optional but recommended: Delete the actual PDF file from disk)
        try:
            # Construct the full filesystem path
            file_path = os.path.join('static', material_to_delete.pdf_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            flash(f"Error deleting file from disk: {e}", "warning")

        # Delete the entry from the database
        db.session.delete(material_to_delete)
        db.session.commit()
        flash('Material deleted successfully.', 'success')
        return redirect(url_for('manage_materials'))

    # --- (for saving the edits) ---
    @app.route('/manage-materials/update/<string:id>', methods=['POST'])
    @login_required
    def update_material(id):
        material_to_update = db.session.get(Material, id)
        if not material_to_update:
            flash('Material not found.', 'danger')
            return redirect(url_for('manage_materials'))

        # Get data from the form
        material_to_update.title = request.form.get('title')
        material_to_update.description = request.form.get('description')
        
        # Check if a new PDF was uploaded
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename != '':
            if allowed_file(pdf_file.filename):
                # --- (Optional) Delete the old PDF file ---
                try:
                    old_file_path = os.path.join('static', material_to_update.pdf_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except OSError as e:
                    flash(f"Error deleting old file: {e}", "warning")
                
                # --- Save the new PDF file ---
                filename = secure_filename(pdf_file.filename)
                save_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'pdfs')
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, filename)
                pdf_file.save(save_path)
                
                # Update the path in the database
                material_to_update.pdf_path = os.path.join('uploads/pdfs', filename).replace('\\', '/')
            else:
                flash('Invalid new file type. Only PDFs are allowed.', 'danger')
                return redirect(url_for('edit_material', id=id))
            
        # Commit changes to the database
        db.session.commit()
        flash('Material updated successfully.', 'success')
        return redirect(url_for('manage_materials'))

    ## Save Material Order Action (from AJAX)
    @app.route('/manage-materials/save-order', methods=['POST'])
    @login_required
    def save_material_order():
        # Get the JSON data sent from the JavaScript
        data = request.json
        if not data or 'order' not in data:
            return jsonify({'error': 'No order data provided'}), 400
        
        id_list = data.get('order')
        
        try:
            # Loop through the list of IDs. The index (0, 1, 2...)
            # will be their new position.
            for index, item_id in enumerate(id_list):
                material = Material.query.filter_by(id=item_id).first()
                if material:
                    material.position = index
                    db.session.add(material)
            
            db.session.commit()
            flash('Material order saved successfully.', 'success')
            return jsonify({'status': 'success', 'message': 'Order saved!'})
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # --- Helper Function for Sorting by Date ---
    def get_sortable_date(page):
        """Safely gets the date from post metadata, converting if necessary."""
        date_val = page.meta.get('date')
        if isinstance(date_val, date): # Handles both date and datetime objects
            # If it's datetime, convert to date; otherwise, it's already a date
            return date_val.date() if isinstance(date_val, datetime) else date_val 
        if isinstance(date_val, str):
            try:
                # Try parsing the standard YYYY-MM-DD format
                return datetime.strptime(date_val, '%Y-%m-%d').date()
            except ValueError:
                # If parsing fails, return a minimum date for consistent sorting
                pass 
        return date.min # Fallback for missing or unparseable dates

    ## Problems of the Month Page
    @app.route('/months-problems')
    def months_problems():
        # Get all published problem pages
        problem_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('months-problems/')]

        # Sort problems using the safer helper function
        sorted_problems_by_date = sorted(problem_pages, key=get_sortable_date, reverse=True)

        # Find the first problem in the sorted list that isn't marked as solved
        current_problem = next((p for p in sorted_problems_by_date if not p.meta.get('is_solved')), None)
        # Get all problems marked as solved
        solved_problems = [p for p in sorted_problems_by_date if p.meta.get('is_solved')]

        return render_template(
            'months-problems.html', 
            logado=current_user.is_authenticated, 
            current_problem=current_problem,
            solved_problems=solved_problems,
            title="Problemas do Mês" # Add title
        )

    ## News Overview Page (Shows sliders)
    @app.route('/news')
    def news():
        # Get all published news pages
        news_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('news/')]
        # Sort news by date (using simpler lambda, assumes date is valid datetime or missing)
        sorted_news = sorted(news_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
        # Filter for award posts
        award_posts = [p for p in sorted_news if p.path.startswith('news/awards/')]
        # Filter for other general news posts
        other_news_posts = [p for p in sorted_news if p.path.startswith('news/others/')]
        return render_template('news.html', 
                               logado=current_user.is_authenticated, 
                               award_posts=award_posts, 
                               other_news_posts=other_news_posts,
                               title="Notícias") # Add title
    
    ## News Awards Page (List View)
    @app.route('/news-awards')
    def news_awards():
        news_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('news/')]
        sorted_news = sorted(news_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
        award_posts = [p for p in sorted_news if p.path.startswith('news/awards/')]
        return render_template(
            'news-awards.html', 
            logado=current_user.is_authenticated, 
            award_posts=award_posts,
            title="Prêmios e Conquistas" # Pass a title for the <title> tag
        )
    
    ## News General Page (List View)
    @app.route('/news-general')
    def news_general():
        news_pages = [p for p in pages if p.meta.get('status') == 'published' and p.path.startswith('news/')]
        sorted_news = sorted(news_pages, key=lambda p: p.meta.get('date', datetime.now()), reverse=True)
        other_news_posts = [p for p in sorted_news if p.path.startswith('news/others/')]
        return render_template(
            'news-general.html', 
            logado=current_user.is_authenticated, 
            other_news_posts=other_news_posts,
            title="Notícias Gerais" # Pass a title for the <title> tag
        )

    ## Team Page (Note: Seems unused currently, template may not exist)
    # @app.route('/team')
    # def team(): return render_template('team.html', logado=current_user.is_authenticated, title="Equipe")

    ## FAQ Page
    @app.route('/faq')
    def faq(): 
        return render_template('faq.html', 
                               logado=current_user.is_authenticated,
                               title="FAQ") # Add title

    ## Contact Page
    @app.route('/contact')
    def contact(): 
        return render_template('contact.html', 
                               logado=current_user.is_authenticated,
                               title="Contato") # Add title

    ## View Single Post Page
    # The <path:path> converter allows slashes in the URL path
    @app.route('/post/<path:path>')
    def view_post(path):
        # Get the FlatPage object or return a 404 error if not found
        post = pages.get_or_404(path)
        # If the post is a draft, only show it to logged-in users
        if post.meta.get('status') == 'draft' and not current_user.is_authenticated:
            abort(404) # Return 404 for non-logged-in users trying to view drafts

        # Find the author's User object based on email in metadata, if provided
        author = None
        author_email = post.meta.get('author_email')
        if author_email:
            author = User.query.filter_by(email=author_email).first()

        # --- HTML Sanitization using Bleach ---
        # Define allowed HTML tags (start with defaults and add necessary ones)
        allowed_tags = list(bleach.sanitizer.ALLOWED_TAGS) + [
            'h1', 'h2', 'h3', 'p', 'br', 'img', 'a', 'ul', 'li', 'ol',
            'strong', 'em', 'u', 's', 'blockquote', 'pre', 'code',
            'video', 'iframe',
            'div'
        ]
        # Define allowed attributes for specific tags
        allowed_attrs = {
            **bleach.sanitizer.ALLOWED_ATTRIBUTES, # Include default allowed attributes
            'img': ['src', 'alt', 'title', 'width', 'height'],
            'video': ['src', 'width', 'height', 'controls', 'preload', 'muted', 'loop', 'autoplay', 'playsinline'],
            'a': ['href', 'title', 'class'],
            'iframe': ['src', 'width', 'height', 'frameborder', 'allow', 'allowfullscreen', 'title'],
            'div': ['class']
        }
        # Sanitize the HTML rendered from Markdown to prevent XSS attacks
        post_html = bleach.clean(
            post.html, # The HTML generated by Flask-FlatPages' Markdown processor
            tags=allowed_tags,
            attributes=allowed_attrs
        )
        # --- End Sanitization ---

        # --- Process and Sanitize Solution Content ---
        solution_html = "" # Initialize as empty string
        if post.path.startswith('months-problems/') and post.meta.get('is_solved'):
            # 2. Get the raw solution markdown from metadata
            raw_solution = post.meta.get('solution_content', '')
            if raw_solution:
                # 3. Convert the solution markdown to HTML
                html_solution = markdown.markdown(raw_solution)
                # 4. Sanitize the new HTML using the *exact same* rules
                solution_html = bleach.clean(
                    html_solution,
                    tags=allowed_tags,
                    attributes=allowed_attrs
                )
        # --- END OF BLOCK ---

        # Render the template to display the post
        return render_template('view-post-flat.html', 
                               post=post, 
                               author=author, 
                               logado=current_user.is_authenticated, 
                               post_html=post_html,
                               solution_html=solution_html,
                               title=post.meta.get('title', 'Post')) # Use post title for page title

    # --- Admin Routes ---

    ## Account Settings Page
    @app.route('/account-settings', methods=['GET', 'POST'])
    @login_required # Protect this route
    def account_settings():
        if request.method == 'POST':
            # Verify current password before allowing changes
            if not current_user.check_password(request.form.get('current_password')):
                flash('Incorrect password. Please try again.', 'danger')
                return redirect(url_for('account_settings'))

            user = current_user # Get the currently logged-in user object
            
            # Check if the new email is different and already exists
            new_email = request.form.get('email')
            if new_email != user.email and User.query.filter_by(email=new_email).first():
                flash('That email address is already in use.', 'danger')
                return redirect(url_for('account_settings'))

            # Update user fields
            user.email = new_email
            user.name = request.form.get('name')
            user.about_me = request.form.get('about_me')

            # Update password only if a new one is provided
            new_password = request.form.get('password')
            if new_password:
                user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

            # Handle profile picture upload
            if 'profile_pic' in request.files:
                profile_pic = request.files['profile_pic']
                if profile_pic.filename != '': # Check if a file was actually selected
                    filename = secure_filename(profile_pic.filename) # Sanitize filename
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    profile_pic.save(image_path)
                    user.profile_image_path = image_path # Update user's profile image path

            # Commit changes to the database
            db.session.commit()
            flash('Your settings have been updated successfully!', 'success')
            return redirect(url_for('account_settings'))
        
        # Render the settings page for GET requests
        return render_template('account-settings.html', 
                               logado=current_user.is_authenticated,
                               title="Account Settings") # Add title

    ## Edit Post Page (Loads content into editor)
    @app.route('/edit-post/<path:path>')
    @login_required # Protect this route
    def post_editor(path): # Changed default path=None as it's required by the route
        post_data = {} # Dictionary to hold post data for the template
        # Construct the full path to the markdown file
        filepath = os.path.join(app.config['FLATPAGES_ROOT'], path + '.md')

        if os.path.exists(filepath):
            try:
                # Read the entire raw content of the file (including front-matter)
                with open(filepath, 'r', encoding='utf-8') as f:
                    full_raw_content = f.read()

                # Use FlatPages to parse the metadata separately
                page = pages.get(path) 
                if page:
                    post_data = page.meta # Get metadata (title, date, etc.)
                    post_data['path'] = path # Add path for context
                    post_data['title'] = page.meta.get('title', 'Untitled') # Ensure title exists
                    post_data['content'] = full_raw_content # Add the raw content for the editor
                else:
                     # This might happen if the file exists but FlatPages fails to parse it
                     flash("Error parsing post metadata.", "warning")
                     return redirect(url_for('index')) # Redirect to index on parsing error

            except Exception as e:
                flash(f"Error reading file: {e}", "danger")
                return redirect(url_for('index')) # Redirect on file read error
        else:
            flash("Post file not found.", "warning")
            return redirect(url_for('index')) # Redirect if file doesn't exist

        # Render the editor template with the loaded post data
        return render_template('post-editor.html', 
                               post=post_data, 
                               logado=current_user.is_authenticated,
                               title=f"Edit: {post_data.get('title', 'Post')}") # Use post title

    ## Save Post Action (Handles POST from editor)
    @app.route('/save-post/<path:path>', methods=['POST'])
    @login_required
    def save_post(path):
        # Get the full new content submitted from the editor textarea
        full_new_content = request.form.get('content')
        # Construct the full path to the markdown file
        filepath = os.path.join(app.config['FLATPAGES_ROOT'], path + '.md')

        # Security check: Ensure the file we are about to overwrite actually exists
        if not os.path.exists(filepath):
             # Return a JSON error
             return jsonify({'status': 'error', 'message': f'Error: Cannot save, original file not found at {filepath}'}), 404

        try:
            # Write the new content, overwriting the old file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_new_content)
            
            # Reload FlatPages cache to reflect changes immediately
            pages.reload() 

            # Instead of redirecting, return success JSON
            return jsonify({'status': 'success', 'message': 'Post saved!'})
            
        except Exception as e:
            flash(f"Error saving file: {e}", "danger")
            # Redirect back to the editor if saving failed
            return redirect(url_for('post_editor', path=path))

    ## Create New Post Page (Shows blank editor with template)
    @app.route('/create-post')
    @login_required # Protect this route
    def create_post_view():
        # Render the create post template
        return render_template('create-post.html', 
                               logado=current_user.is_authenticated,
                               title="Create New Post") # Add title

    ## Create New Post Action (Handles POST from create form)
    @app.route('/create-post-save', methods=['POST'])
    @login_required
    def create_post_save():
        full_content = request.form.get('full_content')
        if not full_content:
            # Return a JSON error instead of flashing
            return jsonify({'status': 'error', 'message': 'Content cannot be empty.'}), 400

        # --- Parse Metadata and Content ---
        try:
            match = re.match(r'^---\s*(.*?)\s*---\s*(.*)', full_content, re.DOTALL)
            if not match: raise ValueError("Could not find YAML front-matter separator '---'")

            yaml_string = match.group(1)
            metadata = yaml.safe_load(yaml_string)
            if not metadata or not isinstance(metadata, dict):
                raise ValueError("Invalid YAML front-matter format")

            title = metadata.get('title')
            if not title: raise ValueError("Metadata must contain a 'title'")

        except (yaml.YAMLError, ValueError) as e:
            # Return a JSON error
            return jsonify({'status': 'error', 'message': f'Error parsing Markdown file: {e}'}), 400
        # --- End Parsing ---

        # --- Determine Filename and Directory (Unchanged) ---
        user_filename = request.form.get('filename_base', '').strip()
        filename_base = slugify.slugify(user_filename) if user_filename else slugify.slugify(title)

        post_type = metadata.get('post_type', 'misc')
        if post_type == 'News':
            category = metadata.get('category', 'General').strip().lower()
            directory = 'news/awards' if category == 'award' else 'news/others'
        elif post_type == 'Month-Problem':
            directory = 'months-problems'
        else:
            directory = 'misc' 

        # --- Check for Existing Files and Generate Unique Name (Unchanged) ---
        counter = 0
        filename = f"{filename_base}.md"
        filepath = os.path.join(app.config['FLATPAGES_ROOT'], directory, filename)
        while os.path.exists(filepath):
            counter += 1
            filename = f"{filename_base}-{counter}.md"
            filepath = os.path.join(app.config['FLATPAGES_ROOT'], directory, filename)
        # --- End File Naming ---
        
        # --- Save the File ---
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            pages.reload()

            page_path = os.path.join(directory, filename_base + (f"-{counter}" if counter > 0 else ""))
            
            # Instead of flashing and redirecting, return success JSON
            return jsonify({
                'status': 'success',
                'message': 'Post created successfully!',
                'new_path': page_path,
                'edit_url': url_for('post_editor', path=page_path) # Pre-generate the URL for JS
            })

        except IOError as e:
            flash(f"Error saving file: {e}", "danger")
            return redirect(url_for('create_post_view'))
        # --- End Save ---

    ## Delete Post Action (Handles POST from button/form)
    @app.route('/delete-post/<path:path>', methods=['POST'])
    @login_required # Protect this route
    def delete_post_file(path):
        # Construct the full path to the markdown file
        filepath = os.path.join(app.config['FLATPAGES_ROOT'], path + '.md')

        if os.path.exists(filepath):
            try:
                # Delete the file from the filesystem
                os.remove(filepath)
                flash(f"Post '{path}' deleted successfully.", "success")
                # Reload FlatPages cache to remove the deleted post
                pages.reload()
                # Redirect back to the drafts page (or another appropriate page)
                return redirect(url_for('drafts'))
            except OSError as e:
                flash(f"Error deleting file: {e}", "danger")
                return redirect(url_for('drafts')) # Redirect even if deletion fails
        else:
            flash("Error: Post file not found.", "warning")
            return redirect(url_for('drafts')) # Redirect if file doesn't exist

    ## Drafts Page (Lists posts marked as draft)
    @app.route('/drafts')
    @login_required # Protect this route
    def drafts():
        # Get all pages with status 'draft'
        draft_pages = [p for p in pages if p.meta.get('status') == 'draft']
        # Sort drafts by date, newest first (using min date as fallback)
        sorted_drafts = sorted(draft_pages, key=lambda p: p.meta.get('date', datetime.min), reverse=True)
        # Render the drafts template
        return render_template('drafts.html', 
                               post_list=sorted_drafts, 
                               logado=current_user.is_authenticated,
                               title="Drafts") # Add title

    # --- Asset Upload Helper ---
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'webm', 'mp4', 'mp3', 'wav', 'ogg', 'svg', 'pdf', 'mov'}
    
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    ## ⬆️ Upload Asset Endpoint (UPDATED)
    @app.route('/upload-asset', methods=['POST'])
    @login_required
    def upload_asset():
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # --- NEW: Context-Aware Path Logic ---
        # Get the desired subfolder path (e.g., "news/my-post")
        post_path = request.form.get('post_path', '')
        
        # Sanitize the subfolder path to prevent directory traversal
        # We split by '/' and secure each part, then rejoin
        safe_parts = [secure_filename(part) for part in post_path.split('/') if part not in ('', '.', '..')]
        safe_subfolder = os.path.join(*safe_parts)
        
        # Define the full target directory
        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], safe_subfolder)
        
        # --- CRITICAL: Path Validation ---
        # Get the absolute paths to prevent any escape
        base_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        target_path = os.path.abspath(target_dir)

        if not target_path.startswith(base_path):
             return jsonify({'error': 'Invalid path specified'}), 403
        
        # Create the directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        # --- End Path Logic ---

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(target_dir, filename)
            
            try:
                file.save(save_path)
                
                # Create the relative path for the URL
                url_path = os.path.join('uploads', safe_subfolder, filename).replace('\\', '/')
                file_url = url_for('static', filename=url_path)

                # Generate the correct Markdown link
                file_extension = filename.rsplit('.', 1)[1].lower()
                if file_extension in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}:
                    markdown_link = f"![{filename}]({file_url})"
                else:
                    markdown_link = f"[{filename}]({file_url})"

                return jsonify({'markdownLink': markdown_link}), 200

            except Exception as e:
                return jsonify({'error': f'Failed to save file: {str(e)}'}), 500
        else:
            return jsonify({'error': 'File type not allowed'}), 400

    ## 🖼️ List Assets Endpoint (NEW)
    @app.route('/list-assets', methods=['GET'])
    @login_required
    def list_assets():
        post_path = request.args.get('post_path', '')
        
        # Sanitize the subfolder path (same logic as upload)
        safe_parts = [secure_filename(part) for part in post_path.split('/') if part not in ('', '.', '..')]
        safe_subfolder = os.path.join(*safe_parts)
        target_dir = os.path.join(app.config['UPLOAD_FOLDER'], safe_subfolder)
        
        # --- CRITICAL: Path Validation ---
        base_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        target_path = os.path.abspath(target_dir)

        if not target_path.startswith(base_path) or not os.path.isdir(target_path):
             return jsonify({'error': 'Invalid path or directory not found'}), 404
        
        files = []
        try:
            for filename in os.listdir(target_dir):
                # Only list files, not subdirectories
                if os.path.isfile(os.path.join(target_dir, filename)):
                    url_path = os.path.join('uploads', safe_subfolder, filename).replace('\\', '/')
                    file_url = url_for('static', filename=url_path)
                    files.append({
                        'name': filename,
                        'url': file_url,
                        'path': os.path.join(safe_subfolder, filename).replace('\\', '/') # Relative path for delete
                    })
            # Sort files by name
            files.sort(key=lambda f: f['name'])
            return jsonify(files)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    ## 🗑️ Delete Asset Endpoint (NEW)
    @app.route('/delete-asset', methods=['POST'])
    @login_required
    def delete_asset():
        file_path = request.json.get('file_path')
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400

        # --- CRITICAL: Path Validation ---
        # Sanitize the file path. os.path.normpath resolves any '..'
        safe_path = os.path.normpath(os.path.join(app.config['UPLOAD_FOLDER'], file_path))
        base_path = os.path.abspath(app.config['UPLOAD_FOLDER'])
        
        if not os.path.abspath(safe_path).startswith(base_path):
            return jsonify({'error': 'Permission denied: Invalid path'}), 403

        try:
            if os.path.exists(safe_path) and os.path.isfile(safe_path):
                os.remove(safe_path)
                return jsonify({'status': 'success', 'message': f'File {file_path} deleted.'})
            else:
                return jsonify({'error': 'File not found'}), 404
        except OSError as e:
            return jsonify({'error': f'Error deleting file: {str(e)}'}), 500