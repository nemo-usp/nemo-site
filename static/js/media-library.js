/**
 * =================================
 * NEMO Media Library
 * =================================
 */
function initializeMediaLibrary(editorInstance, getPostPathCallback) {
    
    // --- 1. Get DOM Elements ---
    const modalElement = document.getElementById('mediaLibraryModal');
    const mediaModal = new bootstrap.Modal(modalElement);
    const mediaGrid = document.getElementById('media-grid');
    const mediaUploadForm = document.getElementById('media-upload-form');
    const mediaFileInput = document.getElementById('media-upload-file');
    const mediaUploadBtn = document.getElementById('media-upload-btn');
    const mediaStatusText = document.getElementById('media-status-text');
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    const uploadUrl = document.documentElement.dataset.uploadUrl;
    const deleteUrl = document.documentElement.dataset.deleteUrl;
    const listUrl = document.documentElement.dataset.listUrl;

    let currentPostPath = '';

    // --- 2. Main Function: Load Files ---
    async function loadMediaFiles(postPath) {
        currentPostPath = postPath; 
        mediaGrid.innerHTML = '<p>Loading...</p>'; 

        try {
            const response = await fetch(`${listUrl}?post_path=${encodeURIComponent(postPath)}`);
            if (!response.ok) throw new Error(`Server error: ${response.statusText}`);
            const files = await response.json();
            if (files.error) throw new Error(files.error);

            if (files.length === 0) {
                mediaGrid.innerHTML = '<p>Nenhum arquivo encontrado. Faça o upload!</p>';
                return;
            }

            let gridHTML = '';
            files.forEach(file => {
                const isImg = isImage(file.name);
                const isVid = isVideo(file.name); // NEW: Check if video

                gridHTML += `
                    <div class="media-item"> 
                        <div class="media-preview" 
                             data-file-url="${file.url}" 
                             data-file-name="${file.name}" 
                             data-is-image="${isImg}"
                             data-is-video="${isVid}"> ${isImg ? 
                                `<img src="${file.url}" alt="${file.name}" loading="lazy">` : 
                                (isVid ? 
                                    `<span class="video-icon">🎥</span>` : // NEW: Show video icon
                                    `<span class="file-icon">📄</span>`
                                )
                            }
                            <span class="file-name">${file.name}</span>
                        </div>
                        <button class="btn btn-danger btn-sm delete-media-btn" data-file-path="${file.path}" title="Delete File">X</button>
                    </div>
                `;
            });
            mediaGrid.innerHTML = gridHTML;
        } catch (error) {
            console.error('Error loading media:', error);
            mediaGrid.innerHTML = `<p class="text-danger">Error loading media: ${error.message}</p>`;
        }
    }

    // --- 3. Event Listeners ---
    modalElement.addEventListener('show.bs.modal', function() {
        const postPath = getPostPathCallback();
        loadMediaFiles(postPath);
    });

    mediaUploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (mediaFileInput.files.length === 0) {
            mediaStatusText.textContent = 'Please select a file first.';
            mediaStatusText.className = 'text-warning';
            return;
        }

        mediaUploadBtn.disabled = true;
        mediaUploadBtn.textContent = 'Uploading...';
        mediaStatusText.textContent = '';

        const formData = new FormData();
        formData.append('file', mediaFileInput.files[0]);
        formData.append('post_path', currentPostPath); 

        try {
            const response = await fetch(uploadUrl, {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            mediaStatusText.textContent = 'Upload successful!';
            mediaStatusText.className = 'text-success';
            mediaFileInput.value = '';
            
            const fileUrl = data.markdownLink.match(/\((.*?)\)/)[1];
            const fileName = data.markdownLink.match(/\[(.*?)\]/)[1];
            const isImg = isImage(fileName);
            const isVid = isVideo(fileName); // NEW: Check if video
            
            // NEW: Updated insert logic
            const insertCode = isImg ?
                `<img src="${fileUrl}" alt="${fileName}" width="100%">` :
                (isVid ? 
                    `<video src="${fileUrl}" width="100%" controls preload="metadata"></video>` : 
                    `<a href="${fileUrl}">${fileName}</a>`
                );
            
            insertTextAtCursor(insertCode);
            loadMediaFiles(currentPostPath);

        } catch (error) {
            console.error('Upload failed:', error);
            mediaStatusText.textContent = `Upload failed: ${error.message}`;
            mediaStatusText.className = 'text-danger';
        } finally {
            mediaUploadBtn.disabled = false;
            mediaUploadBtn.textContent = 'Upload';
        }
    });

    mediaGrid.addEventListener('click', async function(e) {
        const target = e.target;

        // Delete Button Logic (Unchanged)
        if (target.classList.contains('delete-media-btn')) {
            const filePath = target.getAttribute('data-file-path');
            if (!confirm(`Are you sure you want to delete this file?\n${filePath}\nThis cannot be undone.`)) {
                return;
            }
            try {
                const response = await fetch(deleteUrl, { 
                    method: 'POST',
                    body: JSON.stringify({ file_path: filePath }),
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken }
                });
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                
                target.closest('.media-item').remove();
            } catch (error) {
                console.error('Delete failed:', error);
                alert(`Could not delete file: ${error.message}`);
            }
        }
        
        // Insert Logic (Updated)
        const preview = target.closest('.media-preview');
        if (preview) {
            const fileUrl = preview.getAttribute('data-file-url');
            const fileName = preview.getAttribute('data-file-name');
            const isImg = preview.getAttribute('data-is-image') === 'true';
            const isVid = preview.getAttribute('data-is-video') === 'true'; // NEW: Get video data
            
            let insertCode;
            if (isImg) {
                insertCode = `<img src="${fileUrl}" alt="${fileName}" width="100%">`;
            } else if (isVid) {
                // NEW: Handle video insert
                insertCode = `<video src="${fileUrl}" width="100%" controls preload="metadata"></video>`;
            } else {
                insertCode = `<a href="${fileUrl}">${fileName}</a>`;
            }
            
            insertTextAtCursor(insertCode);
            mediaModal.hide();
        }
    });

    // --- 4. Helper Functions ---
    function isImage(filename) {
        return /\.(jpe?g|png|gif|webp|svg)$/i.test(filename);
    }
    
    // NEW: Helper function for videos
    function isVideo(filename) {
        return /\.(mp4|webm|mov)$/i.test(filename);
    }

    function insertTextAtCursor(text) {
        editorInstance.codemirror.replaceSelection(text);
    }
}