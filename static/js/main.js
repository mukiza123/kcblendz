// KCBlendz frontend helpers
(function () {
  // Auto-dismiss flash messages after 5s
  document.querySelectorAll('[data-flash]').forEach(el => {
    setTimeout(() => {
      el.classList.add('flash-exit-a');
      setTimeout(() => el.remove(), 300);
    }, 5000);
  });

  // Format card number input with spaces every 4 digits
  document.querySelectorAll('input[name="card_number"]').forEach(input => {
    input.addEventListener('input', e => {
      const digits = e.target.value.replace(/\D/g, '').slice(0, 19);
      e.target.value = digits.replace(/(.{4})/g, '$1 ').trim();
    });
  });

  // Quantity steppers (data-qty="up|down")
  document.querySelectorAll('[data-qty]').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = document.querySelector(btn.dataset.target);
      if (!target) return;
      let v = parseInt(target.value || '1', 10);
      target.value = Math.max(1, btn.dataset.qty === 'up' ? v + 1 : v - 1);
    });
  });
})();
