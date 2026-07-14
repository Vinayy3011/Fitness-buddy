/**
 * Fitness Buddy AI — Main JavaScript
 * Dark mode, CSRF, toast notifications, scroll animations
 */

// ── CSRF Token ─────────────────────────────────────────────────────────────
// Primary source: <meta name="csrf-token"> injected by base.html on every page.
// Fallback:       hidden input inside a <form> (login / register pages).
function getCSRF() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta) return meta.getAttribute("content");
  const hidden = document.querySelector('input[name="csrf_token"]');
  if (hidden) return hidden.value;
  return "";
}

// Expose globally for inline scripts in Jinja templates
window.getCSRF = getCSRF;

// ── Dark Mode ───────────────────────────────────────────────────────────────
(function initTheme() {
  const stored = localStorage.getItem("fb_theme") || "light";
  applyTheme(stored);
})();

function applyTheme(theme) {
  document.documentElement.setAttribute("data-bs-theme", theme);
  localStorage.setItem("fb_theme", theme);
  const icon = document.getElementById("themeIcon");
  if (icon) {
    icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
  }
  // Re-render any Chart.js charts on theme switch
  if (window._weightChart) {
    const isDark = theme === "dark";
    const gridColor = isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)";
    const textColor = isDark ? "#8892a4" : "#6c757d";
    window._weightChart.options.scales.x.grid.color = gridColor;
    window._weightChart.options.scales.x.ticks.color = textColor;
    window._weightChart.options.scales.y.grid.color = gridColor;
    window._weightChart.options.scales.y.ticks.color = textColor;
    window._weightChart.update();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("themeToggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-bs-theme") || "light";
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }
});

// ── Toast Notifications ─────────────────────────────────────────────────────
window.showToast = function (message, type = "info") {
  const id = "toast-" + Date.now();
  const iconMap = {
    success: "bi-check-circle-fill text-success",
    danger:  "bi-exclamation-triangle-fill text-danger",
    warning: "bi-exclamation-circle-fill text-warning",
    info:    "bi-info-circle-fill text-info",
  };
  const icon = iconMap[type] || iconMap.info;

  const container = document.querySelector(".toast-container")
    || (() => {
      const c = document.createElement("div");
      c.className = "toast-container position-fixed bottom-0 end-0 p-3";
      c.style.zIndex = "9999";
      document.body.appendChild(c);
      return c;
    })();

  container.insertAdjacentHTML("beforeend", `
    <div id="${id}" class="toast align-items-center border-0 mb-2" role="alert">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi ${icon}"></i>
          <span>${message}</span>
        </div>
        <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    </div>
  `);

  const el = document.getElementById(id);
  const t  = new bootstrap.Toast(el, { delay: 3500, autohide: true });
  t.show();
  el.addEventListener("hidden.bs.toast", () => el.remove());
};

// ── Scroll Animations ───────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const targets = document.querySelectorAll("[data-animate]");
  if (!targets.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          observer.unobserve(e.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: "0px 0px -40px 0px" }
  );
  targets.forEach(t => observer.observe(t));
});

// ── Auto-dismiss flash alerts ───────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    document.querySelectorAll(".alert.alert-success, .alert.alert-info").forEach(el => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    });
  }, 5000);
});

// ── Navbar scroll behaviour ─────────────────────────────────────────────────
window.addEventListener("scroll", () => {
  const nav = document.getElementById("mainNavbar");
  if (!nav) return;
  if (window.scrollY > 10) {
    nav.style.boxShadow = "0 2px 20px rgba(0,0,0,0.12)";
  } else {
    nav.style.boxShadow = "none";
  }
}, { passive: true });

// ── Number counter animation ─────────────────────────────────────────────────
function animateCounter(el, target, duration = 800) {
  const start = parseInt(el.textContent) || 0;
  const step  = (target - start) / (duration / 16);
  let current = start;
  const timer = setInterval(() => {
    current += step;
    if ((step > 0 && current >= target) || (step < 0 && current <= target)) {
      clearInterval(timer);
      el.textContent = target;
    } else {
      el.textContent = Math.round(current);
    }
  }, 16);
}

// Animate dashboard stat numbers on page load
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".stat-value").forEach(el => {
    const val = parseFloat(el.textContent);
    if (!isNaN(val) && val > 0) {
      el.textContent = "0";
      setTimeout(() => animateCounter(el, val), 300);
    }
  });
});

// ── Prevent double-form submission ─────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", (e) => {
      const btn = form.querySelector('[type="submit"]');
      if (btn && !btn.disabled) {
        btn.disabled = true;
        setTimeout(() => { btn.disabled = false; }, 5000);
      }
    });
  });
});
