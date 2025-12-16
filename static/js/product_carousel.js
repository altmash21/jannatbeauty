// Product Carousel - Infinite Loop Swiper
// Force infinite looping with manual slide cloning if needed

(function () {
    'use strict';

    // Signal legacy scripts to skip their product carousel initialization
    window.disableLegacyProductCarousel = true;

    function initProductCarousels() {
        // Clean up any existing instances
        if (window.productSwiperInstances) {
            window.productSwiperInstances.forEach(instance => {
                if (instance && typeof instance.destroy === 'function') {
                    try {
                        instance.destroy(true, true);
                    } catch (e) {
                        console.log('Error destroying swiper:', e);
                    }
                }
            });
        }
        window.productSwiperInstances = [];

        document.querySelectorAll('.product-swiper').forEach(function (carousel, index) {
            // Destroy any swiper instance that might still be attached
            if (carousel.swiper && typeof carousel.swiper.destroy === 'function') {
                try {
                    carousel.swiper.destroy(true, true);
                } catch (e) {
                    console.log('Error destroying existing swiper:', e);
                }
            }

            const wrapper = carousel.querySelector('.swiper-wrapper');
            if (!wrapper) {
                console.error('No swiper-wrapper found in carousel', index);
                return;
            }

            const slides = carousel.querySelectorAll('.swiper-slide:not(.swiper-slide-duplicate)');
            const slideCount = slides.length;

            console.log('Carousel', index, '- Found', slideCount, 'slides');

            if (slideCount === 0) {
                console.warn('No slides found in carousel', index);
                return;
            }

            // Only enable loop if we have more than 1 slide
            const enableLoop = slideCount > 1;

            // Calculate loopAdditionalSlides to ensure smooth looping
            // Need extra slides equal to the number visible at once
            const loopAdditionalSlides = Math.max(4, slideCount);

            // Swiper configuration
            const swiperConfig = {
                // Loop configuration
                loop: enableLoop,
                loopedSlides: enableLoop ? slideCount : 0,
                loopAdditionalSlides: enableLoop ? loopAdditionalSlides : 0,
                loopFillGroupWithBlank: false,

                // Slides per view - whole numbers only, no partial slides
                slidesPerView: 2,
                slidesPerGroup: 1,
                spaceBetween: 12,

                // Speed and easing
                speed: 600,

                // Allow touch
                grabCursor: true,
                touchRatio: 1,
                allowTouchMove: true,

                // Autoplay - only if loop is enabled, starts when section is in view
                autoplay: false, // Start disabled, will be enabled via Intersection Observer

                // Responsive breakpoints - whole numbers only
                breakpoints: {
                    640: {
                        slidesPerView: 3,
                        slidesPerGroup: 1,
                        spaceBetween: 20,
                    },
                    1024: {
                        slidesPerView: 4,
                        slidesPerGroup: 1,
                        spaceBetween: 24,
                    },
                    1280: {
                        slidesPerView: 4,
                        slidesPerGroup: 1,
                        spaceBetween: 30,
                    }
                },

                // Navigation
                navigation: {
                    nextEl: carousel.querySelector('.swiper-button-next'),
                    prevEl: carousel.querySelector('.swiper-button-prev'),
                },

                // Pagination
                pagination: {
                    el: carousel.querySelector('.swiper-pagination'),
                    clickable: true,
                    dynamicBullets: true,
                },

                // Critical for loop
                watchSlidesProgress: true,
                watchSlidesVisibility: true,
                observer: true,
                observeParents: true,
                observeSlideChildren: true,

                // Prevent partial slides
                centeredSlides: false,
                centeredSlidesBounds: false,
                watchOverflow: true,

                // Events to debug
                on: {
                    init: function () {
                        console.log('Swiper', index, 'initialized - isEnd:', this.isEnd, 'isBeginning:', this.isBeginning, 'loop:', this.params.loop, 'slides:', slideCount);
                    },
                    slideChange: function () {
                        console.log('Slide changed - activeIndex:', this.activeIndex, 'realIndex:', this.realIndex, 'isEnd:', this.isEnd);

                        // If we've reached the end, wait for autoplay delay then loop back smoothly
                        if (this.isEnd && enableLoop && this.autoplay && this.autoplay.running) {
                            console.log('Reached end - will loop back after delay');
                            const swiperInstance = this;

                            // Stop autoplay temporarily
                            this.autoplay.stop();

                            // Wait for the autoplay delay (3000ms) then smoothly transition back
                            setTimeout(function () {
                                swiperInstance.slideTo(0, 600); // Smooth 600ms transition
                                // Restart autoplay after a brief moment
                                setTimeout(function () {
                                    if (swiperInstance.autoplay) {
                                        swiperInstance.autoplay.start();
                                    }
                                }, 700); // Start after transition completes
                            }, 3000); // Match the autoplay delay
                        }
                    },
                    reachEnd: function () {
                        console.log('Reached end event fired');
                    }
                }
            };

            try {
                const swiper = new Swiper(carousel, swiperConfig);
                window.productSwiperInstances.push(swiper);
                console.log('Swiper', index, 'successfully initialized with loop');

                // Setup Intersection Observer to start autoplay when section is visible
                if (enableLoop && 'IntersectionObserver' in window) {
                    const observer = new IntersectionObserver((entries) => {
                        entries.forEach(entry => {
                            if (entry.isIntersecting) {
                                // Section is visible, start autoplay
                                if (swiper.autoplay && !swiper.autoplay.running) {
                                    swiper.params.autoplay = {
                                        delay: 3000,
                                        disableOnInteraction: false,
                                        pauseOnMouseEnter: true,
                                        stopOnLastSlide: false,
                                        reverseDirection: false,
                                    };
                                    swiper.autoplay.start();
                                    console.log('Autoplay started for carousel', index);
                                }
                            } else {
                                // Section is not visible, stop autoplay
                                if (swiper.autoplay && swiper.autoplay.running) {
                                    swiper.autoplay.stop();
                                    console.log('Autoplay stopped for carousel', index);
                                }
                            }
                        });
                    }, {
                        threshold: 0.3 // Start when 30% of section is visible
                    });

                    observer.observe(carousel);
                }
            } catch (e) {
                console.error('Error initializing swiper', index, ':', e);
            }
        });
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initProductCarousels);
    } else {
        // DOM already loaded
        setTimeout(initProductCarousels, 100);
    }
})();
