// script.js

document.addEventListener('DOMContentLoaded', () => {
  AOS.init();

  // Animate education progress circles
  const circles = document.querySelectorAll('.progress-circle');
  circles.forEach(circle => {
    const percent = Math.min(parseInt(circle.getAttribute('data-percent')) || 0, 100);
    const circlePath = circle.querySelector('.circle');
    const percentageText = circle.querySelector('.percentage-text');
    if (!circlePath || !percentageText) return;

    const radius = 15.9155; // SVG circle radius from your path
    const circumference = 2 * Math.PI * radius;

    let progress = 0;
    const duration = 1400; 
    const stepTime = 12;
    const steps = duration / stepTime;
    const increment = percent / steps;

    function animateStep() {
      progress += increment;
      if (progress > percent) progress = percent;
      const dashArray = (progress / 100) * circumference;
      circlePath.style.strokeDasharray = `${dashArray} ${circumference}`;
      percentageText.textContent = `${Math.round(progress)}%`;
      if (progress < percent) {
        setTimeout(animateStep, stepTime);
      }
    }
    animateStep();
  });

  // Projects - On hover show "Tap to play" overlay, on click open YouTube embed modal
  const projectsGrid = document.querySelector('.projects-grid');

  // Create modal for video player
  const videoModal = document.createElement('div');
  videoModal.className = 'modal video-modal';
  videoModal.innerHTML = `
    <div class="modal-content video-content">
      <span class="close" aria-label="Close video modal">&times;</span>
      <div class="video-wrapper" tabindex="0">
        <iframe src="" frameborder="0" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>
      </div>
    </div>
  `;
  document.body.appendChild(videoModal);

  const videoIframe = videoModal.querySelector('iframe');
  const videoCloseBtn = videoModal.querySelector('.close');

  videoCloseBtn.addEventListener('click', () => {
    closeVideoModal();
  });

  videoModal.addEventListener('click', e => {
    if (e.target === videoModal) {
      closeVideoModal();
    }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && videoModal.classList.contains('active')) {
      closeVideoModal();
    }
  });

  function closeVideoModal() {
    videoIframe.src = '';
    videoModal.classList.remove('active');
    lastFocusedProject?.focus();
    lastFocusedProject = null;
  }

  let lastFocusedProject = null;
  projectsGrid.querySelectorAll('.project-card').forEach(card => {
    // Add overlay element for hover
    const overlay = document.createElement('div');
    overlay.className = 'project-overlay';
    overlay.textContent = 'Tap to play ▶';
    card.appendChild(overlay);

    // Hover show overlay
    card.addEventListener('mouseenter', () => {
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
    });
    card.addEventListener('mouseleave', () => {
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
    });

    // Click to open modal and play video
    card.addEventListener('click', e => {
      e.preventDefault();
      const videoURL = card.getAttribute('href');
      if (!videoURL) return;
      lastFocusedProject = card;
      const embedUrl = convertYoutubeURLToEmbed(videoURL);
      if (!embedUrl) return alert('Invalid YouTube URL.');
      videoIframe.src = embedUrl + '?autoplay=1&rel=0&showinfo=0';
      videoModal.classList.add('active');
      videoIframe.focus();
    });

    // Accessibility: show overlay also on focus and hide on blur
    card.addEventListener('focus', () => {
      overlay.style.opacity = '1';
      overlay.style.pointerEvents = 'auto';
    });
    card.addEventListener('blur', () => {
      overlay.style.opacity = '0';
      overlay.style.pointerEvents = 'none';
    });
  });

  // Helper: convert youtube watch link to embed URL
  function convertYoutubeURLToEmbed(url) {
    try {
      const u = new URL(url);
      if (
        u.hostname.includes('youtu.be')
      ) {
        return 'https://www.youtube.com/embed/' + u.pathname.slice(1);
      } else if (
        u.hostname.includes('youtube.com')
      ) {
        const v = u.searchParams.get('v');
        if (v) return 'https://www.youtube.com/embed/' + v;
      }
    } catch {
      return null;
    }
    return null;
  }

  // Chatbot implementation

  const chatToggle = document.querySelector('.chat-float');
  const chatBox = document.getElementById('chat-box');
  const chatCloseBtn = chatBox.querySelector('.chat-close');
  const chatBody = document.getElementById('chat-body');
  const userInput = document.getElementById('user-input');

  // Toggle chat box visibility
  function toggleChat(preserveFocus = false) {
    const isOpen = chatBox.classList.contains('active');
    if (isOpen) {
      chatBox.classList.remove('active');
      if (!preserveFocus) chatToggle.focus();
    } else {
      chatBox.classList.add('active');
      userInput.focus();
    }
  }
  window.toggleChat = toggleChat;

  chatToggle.addEventListener('click', () => toggleChat());
  chatCloseBtn.addEventListener('click', () => toggleChat());

  // Predefined bot responses keywords
  const botKeywords = {
    greetings: ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening'],
    farewell: ['bye', 'goodbye', 'see you', 'farewell'],
    skills: ['skills', 'technology', 'technologies', 'stack'],
    projects: ['projects', 'work', 'portfolio'],
    contact: ['contact', 'email', 'phone', 'reach'],
    help: ['help', 'assist', 'support', 'question'],
    codingProfiles: ['hackerrank', 'leetcode', 'codechef']
  };

  // Add chat bubble (sender: 'bot' or 'user')
  function addChatBubble(text, sender = 'bot') {
    const bubble = document.createElement('div');
    bubble.classList.add('chat-bubble', sender);
    bubble.textContent = text;
    chatBody.appendChild(bubble);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Check if input contains any keyword arrays
  function containsKeyword(text, keywordGroup) {
    return keywordGroup.some(word => text.includes(word));
  }

  // Generate bot response by keyword matching
  function getBotResponse(message) {
    const msg = message.toLowerCase();

    if (containsKeyword(msg, botKeywords.greetings)) {
      return "Hello! I'm DevBot 🤖. You can ask me about my projects, skills, or coding profiles.";
    }
    if (containsKeyword(msg, botKeywords.farewell)) {
      return "Goodbye! Feel free to chat anytime.";
    }
    if (containsKeyword(msg, botKeywords.skills)) {
      return "My skills include C, Java, HTML, CSS, JavaScript, Python, and more.";
    }
    if (containsKeyword(msg, botKeywords.projects)) {
      return "You can explore my projects section for websites, games, and simulations.";
    }
    if (containsKeyword(msg, botKeywords.contact)) {
      return "You can contact me via the form or email me at devashish8275@gmail.com.";
    }
    if (containsKeyword(msg, botKeywords.codingProfiles)) {
      return "I am active on HackerRank, LeetCode, and CodeChef. Check the Coding Profiles section for links.";
    }
    if (containsKeyword(msg, botKeywords.help)) {
      return "I'm here to help! Try asking about my skills, projects, coding profiles, or contact info.";
    }

    return "Sorry, I didn't understand that. Could you rephrase?";
  }

  // Handle sending a message
  function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    addChatBubble(message, 'user');
    userInput.value = '';
    setTimeout(() => {
      addChatBubble(getBotResponse(message), 'bot');
    }, 500);
  }
  window.sendMessage = sendMessage;

  userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Voice recognition support
  window.startVoiceInput = function () {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Voice recognition is not supported in your browser.');
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.start();

    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      userInput.value = transcript;
      sendMessage();
    };

    recognition.onerror = function (event) {
      alert('Voice recognition error: ' + event.error);
    };
  };

  // Contact form validation and simulated submission
  const contactForm = document.querySelector('.contact-form');
  contactForm?.addEventListener('submit', e => {
    e.preventDefault();

    const [nameInput, emailInput, messageInput] = contactForm.querySelectorAll('input, input[type="email"], textarea');

    [nameInput, emailInput, messageInput].forEach(el => el.style.borderColor = '#bfc7d4');

    if (nameInput.value.trim().length < 3) {
      alert('Please enter at least 3 characters for name.');
      nameInput.style.borderColor = 'red';
      nameInput.focus();
      return;
    }
    if (!validateEmail(emailInput.value.trim())) {
      alert('Please enter valid email address.');
      emailInput.style.borderColor = 'red';
      emailInput.focus();
      return;
    }
    if (messageInput.value.trim().length < 10) {
      alert('Message should be at least 10 characters.');
      messageInput.style.borderColor = 'red';
      messageInput.focus();
      return;
    }

    const submitBtn = contactForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = "Sending...";

    // Simulate send delay
    setTimeout(() => {
      alert('Thank you for reaching out! I will get back to you soon.');
      contactForm.reset();
      submitBtn.disabled = false;
      submitBtn.textContent = "Send Message";
    }, 1800);
  });

  function validateEmail(email) {
    const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@(([^<>()[\]\\.,;:\s@"]+\.)+[^<>()[\]\\.,;:\s@"]{2,})$/i;
    return re.test(String(email).toLowerCase());
  }

});