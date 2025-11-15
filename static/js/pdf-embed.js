// Import the PDF.js library components needed.
// Assumes pdf.mjs is located relative to this script file.
import * as pdfjsLib from '../pdfjs/build/pdf.mjs'; //

// Wait until the basic HTML structure of the page is ready.
document.addEventListener("DOMContentLoaded", function() {
    
    // Set the path to the PDF.js worker script. This is required by the library.
    // The path should be relative to the web server's root.
    pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdfjs/build/pdf.worker.mjs'; //

    // Find all anchor (<a>) tags in the document that have the class 'pdf-embed'.
    // These links are expected to point directly to PDF files.
    const pdfLinks = document.querySelectorAll('a.pdf-embed'); //

    // Iterate over each found PDF link.
    pdfLinks.forEach(link => {
        // Get the URL (href attribute) of the PDF file from the link.
        const url = link.href; //
        
        // --- Create DOM elements for the viewer ---
        
        // 1. Create the main container div for this PDF instance.
        const viewerContainer = document.createElement('div');
        viewerContainer.classList.add('pdf-viewer-container'); // Apply styling from pdf-viewer.css
        
        // 2. Create a download button.
        const downloadBtn = document.createElement('a');
        downloadBtn.href = url; // Link directly to the PDF file.
        downloadBtn.textContent = 'Fazer Download do PDF'; // Button text.
        downloadBtn.classList.add('pdf-download-btn'); // Apply styling.
        // Extract the filename from the URL to suggest it for download.
        downloadBtn.setAttribute('download', url.split('/').pop()); //
        
        // 3. Add the download button *inside* the main container.
        viewerContainer.appendChild(downloadBtn); //
        
        // --- Replace the original link with the viewer container ---
        // Find the parent node of the original link and replace the link with our new container.
        link.parentNode.replaceChild(viewerContainer, link); //

        // --- Asynchronous function to render all pages of a loaded PDF ---
        // Takes a loaded PDF document object as input.
        const renderAllPages = async (pdf) => {
            // Loop through each page number, from 1 to the total number of pages.
            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) { //
                try {
                    // Asynchronously get the specific page object from the PDF document.
                    const page = await pdf.getPage(pageNum); //
                    
                    // --- Prepare Canvas for Rendering ---
                    const scale = 1.5; // Rendering scale factor (higher = better quality, larger size).
                    // Get the viewport dimensions at the desired scale.
                    const viewport = page.getViewport({ scale: scale }); //

                    // Create a <canvas> element specifically for this page.
                    const canvas = document.createElement('canvas'); //
                    const context = canvas.getContext('2d'); // Get the 2D drawing context.
                    // Set the canvas dimensions to match the PDF page's viewport.
                    canvas.height = viewport.height; //
                    canvas.width = viewport.width; //

                    // Add the canvas to the DOM, placing it *before* the download button within the container.
                    viewerContainer.insertBefore(canvas, downloadBtn); //

                    // --- Render the Page ---
                    // Define the rendering parameters.
                    const renderContext = {
                        canvasContext: context, // The canvas context to draw on.
                        viewport: viewport      // The dimensions and scale to use.
                    };
                    // Asynchronously render the PDF page onto the canvas.
                    // .promise ensures we wait until rendering is complete before logging.
                    await page.render(renderContext).promise; //
                    // console.log(`Page ${pageNum} rendered`); // Optional: Log success

                } catch (pageReason) {
                    // Log an error if rendering a specific page fails.
                    console.error(`Error rendering page ${pageNum}:`, pageReason);
                    // Optionally, display an error message for this specific page in the container.
                    const errorMsg = document.createElement('p');
                    errorMsg.textContent = `Error loading page ${pageNum}.`;
                    errorMsg.style.color = 'red';
                    viewerContainer.insertBefore(errorMsg, downloadBtn);
                }
            }
        };

        // --- Initialize PDF.js Loading ---
        // Start the process of fetching and parsing the PDF document from the URL.
        const loadingTask = pdfjsLib.getDocument(url); //
        // Handle the promise returned by getDocument.
        loadingTask.promise.then(
            function(pdf) { // Success handler: called when the PDF is loaded and parsed.
                // console.log('PDF loaded'); // Optional: Log success
                // Call the function to render all pages into the container.
                renderAllPages(pdf); //
            }, 
            function (reason) { // Error handler: called if loading/parsing fails.
                // Log the error reason to the console.
                console.error("Error loading PDF:", reason); //
                // Display an error message inside the viewer container.
                viewerContainer.textContent = "Error: Could not load PDF."; //
            }
        );
    });
});