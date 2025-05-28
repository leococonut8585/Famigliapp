document.addEventListener('DOMContentLoaded', () => {
  Array.from(document.querySelectorAll('.employee-box')).forEach(box => {
    box.addEventListener('dragstart', e => {
      console.log('dragstart employee-box:', box.dataset.emp);
      e.dataTransfer.setData('text/plain', box.dataset.emp);
      e.dataTransfer.setData('text/from-cell', '');
      e.dataTransfer.effectAllowed = 'move';
    });
  });

  Array.from(document.querySelectorAll('.shift-cell')).forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    function addSpan(span) {
      span.draggable = true;
      span.addEventListener('dragstart', e => {
        console.log('dragstart assigned span:', span.textContent, 'from cell:', cell.dataset.date);
        e.dataTransfer.setData('text/plain', span.textContent);
        e.dataTransfer.setData('text/from-cell', cell.dataset.date);
        e.dataTransfer.effectAllowed = 'move';
      });
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

    Array.from(list.querySelectorAll('.assigned')).forEach(addSpan);

    function handleDrop(e) {
      e.preventDefault();
      console.log('drop on cell:', cell.dataset.date, 'data:', e.dataTransfer.getData('text/plain'));
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
      const originDate = e.dataTransfer.getData('text/from-cell');
      if (originDate && originDate !== cell.dataset.date) {
        const origin = document.querySelector(`.shift-cell[data-date="${originDate}"]`);
        if (origin) {
          const oInput = origin.querySelector('input');
          const oList = origin.querySelector('.assignments');
          let oEmps = oInput.value ? oInput.value.split(',') : [];
          const idx = oEmps.indexOf(emp);
          if (idx >= 0) {
            oEmps.splice(idx, 1);
            oInput.value = oEmps.join(',');
            oList.querySelectorAll('.assigned').forEach(s => {
              if (s.textContent === emp) s.remove();
            });
          }
        }
      }
    }

    cell.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    list.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.effectAllowed = 'move';
    });
    cell.addEventListener('drop', handleDrop);
    list.addEventListener('drop', handleDrop);
  });
});
