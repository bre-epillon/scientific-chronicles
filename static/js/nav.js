document.addEventListener('DOMContentLoaded', () => {
  const todayNavLinks = document.querySelectorAll('#today-nav-link');
  todayNavLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const t = new Date();
      const m = String(t.getMonth() + 1).padStart(2, '0');
      const d = String(t.getDate()).padStart(2, '0');
      window.location.href = `/date/${m}-${d}.html`;
    });
  });

  const randomNavLinks = document.querySelectorAll('#random-nav-link');
  randomNavLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const rDate = new Date(new Date().getFullYear(), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1);
      const m = String(rDate.getMonth() + 1).padStart(2, '0');
      const d = String(rDate.getDate()).padStart(2, '0');
      window.location.href = `/date/${m}-${d}.html`;
    });
  });
});
