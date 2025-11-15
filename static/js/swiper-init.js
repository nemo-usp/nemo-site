//* --- Master Swiper Initialization File --- */
/* This one file controls all sliders on the site. */

document.addEventListener('DOMContentLoaded', function () {

    // --- 1. Initialize Index Page Slider ---
    // UPDATED: This config now matches the news page sliders
    const indexSwiperEl = document.querySelector('#indexSwiper');
    if (indexSwiperEl) {
        var indexSwiper = new Swiper("#indexSwiper", {
            slidesPerView: 1,
            spaceBetween: 25,
            loop: true,
            centeredSlides: true,
            grabCursor: true,
            pagination: {
              el: ".index-pagination", // Kept index-specific class
              clickable: true,
              dynamicBullets: true,
            },
            navigation: {
              nextEl: ".index-next", // Kept index-specific class
              prevEl: ".index-prev", // Kept index-specific class
            },
            breakpoints: {
                576: { // Matches Bootstrap's 'sm' breakpoint
                    slidesPerView: 1,
                    centeredSlides: false,
                },
                992: { // Matches Bootstrap's 'lg' breakpoint
                    slidesPerView: 2,
                    centeredSlides: false,
                },
                 1200: { // ADDED this breakpoint to match news.html
                    slidesPerView: 3,
                    centeredSlides: false
                 },
            },
        });
    }

    // --- 2. Initialize News Page (Awards) Slider ---
    // (This block is unchanged)
    const awardsSwiperEl = document.querySelector('#awardsSwiper');
    if (awardsSwiperEl) {
        var awardsSwiper = new Swiper("#awardsSwiper", {
            slidesPerView: 1,
            spaceBetween: 25,
            loop: true,
            centeredSlides: true,
            grabCursor: true,
            pagination: {
              el: ".awards-pagination",
              clickable: true,
              dynamicBullets: true,
            },
            navigation: {
              nextEl: ".awards-next",
              prevEl: ".awards-prev",
            },
            breakpoints: {
                576: {
                    slidesPerView: 1,
                    centeredSlides: false
                },
                992: {
                    slidesPerView: 2,
                    centeredSlides: false
                 },
                 1200: {
                    slidesPerView: 3,
                    centeredSlides: false
                 },
            },
        });
    }

    // --- 3. Initialize News Page (Other News) Slider ---
    // (This block is unchanged)
    const otherNewsSwiperEl = document.querySelector('#otherNewsSwiper');
    if (otherNewsSwiperEl) {
         var otherNewsSwiper = new Swiper("#otherNewsSwiper", {
            slidesPerView: 1,
            spaceBetween: 25,
            loop: true,
            centeredSlides: true,
            grabCursor: true,
            pagination: {
              el: ".other-pagination",
              clickable: true,
              dynamicBullets: true,
            },
            navigation: {
              nextEl: ".other-next",
              prevEl: ".other-prev",
            },
            breakpoints: {
                576: {
                    slidesPerView: 1,
                    centeredSlides: false
                 },
                992: {
                    slidesPerView: 2,
                    centeredSlides: false
                 },
                1200: {
                     slidesPerView: 3,
                     centeredSlides: false
                 },
            },
        });
    }
});