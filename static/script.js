document.addEventListener('DOMContentLoaded', function () {
  if (typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
  } else {
    console.warn("ScrollTrigger is not defined. Check if the script is loaded correctly.");
  }

  // Cards visibility logic on scroll
  const cards = document.querySelectorAll('.neumorphic-card');

  const showCards = () => {
    const windowHeight = window.innerHeight;
    const scrollY = window.scrollY;

    cards.forEach(card => {
      const cardRect = card.getBoundingClientRect();
      const cardTop = cardRect.top + scrollY;

      if (cardTop < windowHeight + scrollY && cardTop + cardRect.height > scrollY) {
        card.classList.add('card-visible'); // Reveal card
      }
    });
  };

  // Initial visibility check on load
  showCards();
  window.addEventListener('scroll', showCards);
});

function replaceText(element, newText, duration) {
  const chars = newText.split("");
  const timeline = gsap.timeline();

  // Clear previous text and prepare for animation
  element.innerHTML = "";

  chars.forEach((char, index) => {
    const span = document.createElement("span");
    span.innerHTML = char;
    span.style.opacity = 0; // Initially hidden
    element.appendChild(span);

    // Animate the reveal of each character
    timeline.to(span, {
      duration: duration / chars.length,
      opacity: 1,
      ease: "power1.inOut",
      delay: index * (duration / chars.length),
    }, 0);
  });

  // After animation, update text fully
  timeline.call(() => {
    element.innerHTML = newText;
  });
}

window.onload = function () {
  // Animate "Analyze" text on page load
  gsap.from(".small-text", { duration: 1, y: -50, opacity: 0, delay: 0.3 });

  // GSAP ScrollTrigger for "How It Works" section
  ScrollTrigger.create({
    trigger: ".how-it-works",
    start: "top 45%",
    onEnter: () => {
      replaceText(document.getElementById("title"), "Discover How Our Tools Work for You", 2);
      replaceText(document.getElementById("highlight"), 
        "Our innovative tool empowers you to take control of your health. Simply input your symptoms, and our system will analyze them to provide valuable insights.", 4);
    }
  });

  // Hero section animations
  gsap.from(".large h2", {
    scrollTrigger: {
      trigger: '.grid-container',
      start: 'top 50%',
      toggleActions: 'play none none none',
    },
    opacity: 0,
    x: -100,
    duration: 1,
  });

  gsap.from('.large p', {
    scrollTrigger: {
      trigger: '.grid-container',
      start: 'top 50%',
      toggleActions: 'play none none none',
    },
    opacity: 0,
    x: 100,
    duration: 1.2,
  });

  // Horizontal scroll and pinning for grid-container
  gsap.to('.grid-container', {
    xPercent: -100,
    ease: 'power2.inOut',  // Smooth easing for better transition
    scrollTrigger: {
      trigger: '.grid-container',
      start: '-10% top',
      end: '+=2000',    // Adjust for content size
      scrub: 1.5,       // Smooth scrub for smoother transition
      pin: true,        // Pin the container while scrolling
      anticipatePin: 1, // Reduce the jump of the pinned element
    }
  });
  

  // Parallax effect for individual cards
  gsap.to('.card', {
    y: (index) => -30 + index * 10,
    scrollTrigger: {
      trigger: '.grid-container',
      start: 'top top',
      scrub: true,
    }
  });

  // Search section fade-in animation
  gsap.from('.search-section', {
    opacity: 0,
    y: 100,
    scrollTrigger: {
      trigger: '.search-section',
      start: 'top bottom',
      toggleActions: 'play none none none',
    }
  });

  // Footer section fade-in animation
  gsap.from('.footer', {
    opacity: 0,
    y: 50,
    scrollTrigger: {
      trigger: '.footer',
      start: 'top bottom',
      toggleActions: 'play none none none',
    }
  });
};

// Parallax scrolling for elements with "data-speed" attribute
window.addEventListener("scroll", function () {
  document.querySelectorAll(".parallax-layer").forEach(function (layer) {
    const speed = layer.getAttribute("data-speed");
    const yPos = -(window.scrollY * speed);
    layer.style.transform = `translate3d(0px, ${yPos}px, 0px)`;
  });
});

// Ensure buttons always remain visible
gsap.set(".primary-btn, .secondary-btn", { opacity: 1, zIndex: 3000 });
