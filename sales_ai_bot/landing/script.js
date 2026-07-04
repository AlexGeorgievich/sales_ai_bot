/* ============================================
   NexusCode Landing — JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ============================================
  // Navbar scroll effect
  // ============================================
  const navbar = document.getElementById('navbar');
  const handleScroll = () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  };
  window.addEventListener('scroll', handleScroll, { passive: true });

  // ============================================
  // Mobile menu
  // ============================================
  const burger = document.getElementById('burger');
  const navLinks = document.getElementById('navLinks');

  burger.addEventListener('click', () => {
    burger.classList.toggle('active');
    navLinks.classList.toggle('active');
    document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      burger.classList.remove('active');
      navLinks.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // ============================================
  // Scroll reveal — stagger for grids
  // ============================================
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const delay = entry.target.dataset.delay || 0;
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, delay);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -50px 0px', threshold: 0.1 });

  document.querySelectorAll('.services-grid .animate-on-scroll, .testimonials-grid .animate-on-scroll, .vibe-courses-grid .animate-on-scroll, .awards-showcase .animate-on-scroll').forEach((el, i) => {
    el.dataset.delay = i * 100;
  });

  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    revealObserver.observe(el);
  });

  // ============================================
  // Parallax — subtle background shift
  // ============================================
  const parallaxElements = document.querySelectorAll('.hero-bg-img, .brand-bg-img, .cta-bg-img');

  let ticking = false;
  const handleParallax = () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        const scrollY = window.scrollY;
        parallaxElements.forEach(img => {
          const section = img.closest('section') || img.closest('.hero-bg')?.parentElement;
          if (!section) return;
          const rect = section.getBoundingClientRect();
          if (rect.bottom < 0 || rect.top > window.innerHeight) return;
          const yPos = rect.top * 0.08;
          img.style.transform = `translateY(${yPos}px)`;
        });
        ticking = false;
      });
      ticking = true;
    }
  };

  window.addEventListener('scroll', handleParallax, { passive: true });

  // ============================================
  // Hero content fade-in
  // ============================================
  const heroContent = document.querySelector('.hero-content');
  if (heroContent) {
    heroContent.style.opacity = '0';
    heroContent.style.transform = 'translateY(20px)';
    heroContent.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
    setTimeout(() => {
      heroContent.style.opacity = '1';
      heroContent.style.transform = 'translateY(0)';
    }, 150);
  }

  // ============================================
  // Counter animation
  // ============================================
  const counters = document.querySelectorAll('.stat-number[data-target]');
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target);
        const duration = 2000;
        const startTime = performance.now();

        const animate = (currentTime) => {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(eased * target);
          if (progress < 1) requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(counter => counterObserver.observe(counter));

  // ============================================
  // Form tabs
  // ============================================
  const tabs = document.querySelectorAll('.form-tab');
  const formB2B = document.getElementById('formB2B');
  const formB2C = document.getElementById('formB2C');
  const formSuccess = document.getElementById('formSuccess');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      if (tab.dataset.tab === 'b2b') {
        formB2B.classList.remove('hidden');
        formB2C.classList.add('hidden');
      } else {
        formB2B.classList.add('hidden');
        formB2C.classList.remove('hidden');
      }
      formSuccess.classList.add('hidden');
    });
  });

  // ============================================
  // Form submission
  // ============================================
  [formB2B, formB2C].forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());
      console.log('Form submitted:', data);

      form.classList.add('hidden');
      formSuccess.classList.remove('hidden');

      setTimeout(() => {
        form.reset();
        formSuccess.classList.add('hidden');
        form.classList.remove('hidden');
      }, 5000);
    });
  });

  // ============================================
  // Smooth scroll
  // ============================================
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = navbar.offsetHeight + 20;
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  // ============================================
  // Phone input mask
  // ============================================
  document.querySelectorAll('input[type="tel"]').forEach(input => {
    input.addEventListener('input', (e) => {
      let value = e.target.value.replace(/\D/g, '');
      if (value.length > 0) {
        if (value[0] === '7' || value[0] === '8') value = value.substring(1);
        let formatted = '+7';
        if (value.length > 0) formatted += ' (' + value.substring(0, 3);
        if (value.length >= 3) formatted += ') ' + value.substring(3, 6);
        if (value.length >= 6) formatted += '-' + value.substring(6, 8);
        if (value.length >= 8) formatted += '-' + value.substring(8, 10);
        e.target.value = formatted;
      }
    });
  });

  // ============================================
  // Active nav link highlight
  // ============================================
  const sections = document.querySelectorAll('section[id]');
  const navLinksAll = document.querySelectorAll('.nav-links a');

  const highlightNav = () => {
    const scrollPos = window.scrollY + navbar.offsetHeight + 100;
    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute('id');
      if (scrollPos >= top && scrollPos < top + height) {
        navLinksAll.forEach(link => {
          link.style.color = '';
          if (link.getAttribute('href') === `#${id}`) {
            link.style.color = 'var(--text-primary)';
          }
        });
      }
    });
  };

  window.addEventListener('scroll', highlightNav, { passive: true });

});