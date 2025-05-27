document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.employee-box').forEach(box => {
    box.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', box.dataset.emp);
    });
  });

  document.querySelectorAll('.shift-cell').forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    function addSpan(span) {
      span.addEventListener('click', () => {
        const emp = span.textContent;
        let emps = input.value ? input.value.split(',') : [];
        const idx = emps.indexOf(emp);
        if (idx >= 0) {
          emps.splice(idx, 1);
          input.value = emps.join(',');
          span.remove();
        }
      });
    }

    list.querySelectorAll('.assigned').forEach(addSpan);

    cell.addEventListener('dragover', e => e.preventDefault());
    cell.addEventListener('drop', e => {
      e.preventDefault();
      const emp = e.dataTransfer.getData('text/plain');
      if (!emp) return;
      let emps = input.value ? input.value.split(',') : [];
      if (!emps.includes(emp)) {
        emps.push(emp);
        input.value = emps.join(',');
        const span = document.createElement('span');
        span.className = 'assigned';
        span.textContent = emp;
        addSpan(span);
        list.appendChild(span);
      }
    });
  });
});

