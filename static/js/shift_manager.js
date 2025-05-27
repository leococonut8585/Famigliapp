document.addEventListener('DOMContentLoaded', () => {
  let dragged = null;
  let fromCell = null;

  document.querySelectorAll('.employee-box').forEach(box => {
    box.setAttribute('draggable', 'true');
    box.addEventListener('dragstart', e => {
      dragged = box.dataset.emp;
      fromCell = null;
      e.dataTransfer.setData('text/plain', dragged);
      e.dataTransfer.effectAllowed = 'move';
    });
  });

  function setupSpan(span, cell) {
    span.setAttribute('draggable', 'true');
    span.addEventListener('dragstart', e => {
      dragged = span.textContent;
      fromCell = cell;
      e.dataTransfer.setData('text/plain', dragged);
      e.dataTransfer.effectAllowed = 'move';
    });
    span.addEventListener('click', () => {
      const emp = span.textContent;
      const input = cell.querySelector('input');
      let emps = input.value ? input.value.split(',') : [];
      const idx = emps.indexOf(emp);
      if (idx >= 0) {
        emps.splice(idx, 1);
        input.value = emps.join(',');
        span.remove();
      }
    });
  }

  document.querySelectorAll('.shift-cell').forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    list.querySelectorAll('.assigned').forEach(span => setupSpan(span, cell));

    function addEmp(emp) {
      let emps = input.value ? input.value.split(',') : [];
      if (!emps.includes(emp)) {
        emps.push(emp);
        input.value = emps.join(',');
        const span = document.createElement('span');
        span.className = 'assigned';
        span.textContent = emp;
        setupSpan(span, cell);
        list.appendChild(span);
      }
    }

    function handleDrop(e) {
      e.preventDefault();
      if (!dragged) return;
      addEmp(dragged);
      if (fromCell && fromCell !== cell) {
        const oInput = fromCell.querySelector('input');
        const oList = fromCell.querySelector('.assignments');
        let oEmps = oInput.value ? oInput.value.split(',') : [];
        const idx = oEmps.indexOf(dragged);
        if (idx >= 0) {
          oEmps.splice(idx, 1);
          oInput.value = oEmps.join(',');
          oList.querySelectorAll('.assigned').forEach(s => {
            if (s.textContent === dragged) s.remove();
          });
        }
      }
      dragged = null;
      fromCell = null;
    }

    cell.addEventListener('dragover', e => e.preventDefault());
    list.addEventListener('dragover', e => e.preventDefault());
    cell.addEventListener('drop', handleDrop);
    list.addEventListener('drop', handleDrop);
  });
});

