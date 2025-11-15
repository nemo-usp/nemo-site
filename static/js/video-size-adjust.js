function alignVideoToTextMidpoint() {
  const textElement = document.getElementById('text-to-measure');
  const videoElement = document.getElementById('video-to-resize');

  if (textElement && videoElement) {
    // --- Part 1: Sync the width (remains the same) ---
    const textWidth = textElement.offsetWidth;
    videoElement.style.width = `${textWidth}px`;
    videoElement.style.height = 'auto';

    // --- Part 2: Calculate position based on screen size ---
    const textRect = textElement.getBoundingClientRect();
    const isMobile = window.innerWidth <= 1210; // Check if we're on a mobile-sized screen
    
    let finalTopPosition;

    if (window.innerWidth <= 1210) {
      // --- MOBILE LOGIC ---
      // This is the value you will tweak. 0.25 means 25% of the text's height.
      const mobileCorrectionFactor = 0.4; 

      // Calculate the base midpoint using your successful desktop formula
      const baseMidpointY = textRect.top - (textRect.height / 2) + window.scrollY;
      
      // Calculate the offset to nudge the video up
      const correctionOffset = textRect.height * mobileCorrectionFactor;

      // Apply the correction to move the video up
      finalTopPosition = baseMidpointY - correctionOffset;

    } else {
      // --- DESKTOP LOGIC (your existing, working formula) ---
      finalTopPosition = textRect.top - (textRect.height / 2) + window.scrollY;
    }
    
    // --- Part 3: Apply the final calculated position ---
    videoElement.style.top = `${finalTopPosition}px`;
  }
}

// Event listeners remain the same
window.addEventListener('DOMContentLoaded', alignVideoToTextMidpoint);
window.addEventListener('resize', alignVideoToTextMidpoint);