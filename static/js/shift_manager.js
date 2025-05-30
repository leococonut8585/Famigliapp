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
          updateShiftCounts(); // Added this line
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
      updateShiftCounts(); // Call to update counts after drop
    }

    cell.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    list.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move'; // Corrected property
    });
    cell.addEventListener('drop', handleDrop);
    list.addEventListener('drop', handleDrop);
  });

  function updateShiftCounts() {
    const statsSummaryDiv = document.querySelector('.employee-stats-summary');
    if (!statsSummaryDiv) {
      console.error('Error: Employee stats summary element not found.');
      return;
    }
    const currentMonth = statsSummaryDiv.dataset.currentMonth;
    if (!currentMonth) {
      console.error('Error: data-current-month attribute not found on stats summary element.');
      return;
    }

    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2); // Remove "d-" prefix
      const employees = input.value ? input.value.split(',').map(emp => emp.trim()).filter(emp => emp) : [];
      currentAssignments[dateKey] = employees;
    });

    fetch('/calendario/api/shift_counts/recalculate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Consider adding CSRF token if your Flask app uses Flask-WTF CSRF protection globally
        // const csrfToken = document.querySelector('input[name="csrf_token"]');
        // if (csrfToken) { headers['X-CSRFToken'] = csrfToken.value; }
      },
      body: JSON.stringify({
        month: currentMonth,
        assignments: currentAssignments
      })
    })
    .then(response => {
      if (!response.ok) {
        // Attempt to parse error from JSON response, otherwise use status text
        return response.json().then(errData => {
          throw new Error(errData.error || response.statusText || `HTTP error! status: ${response.status}`);
        }).catch(() => { // Fallback if parsing JSON fails
          throw new Error(response.statusText || `HTTP error! status: ${response.status}`);
        });
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        if (data.counts) {
          for (const [emp, workDays] of Object.entries(data.counts)) {
            const workCountSpan = document.querySelector(`.work-count[data-emp="${emp}"]`);
            if (workCountSpan) {
              workCountSpan.textContent = workDays;
            } else {
              console.warn(`Warning: Work count span not found for employee: ${emp}`);
            }
          }
        }
        if (data.off_counts) {
          for (const [emp, offDays] of Object.entries(data.off_counts)) {
            const offCountSpan = document.querySelector(`.off-count[data-emp="${emp}"]`);
            if (offCountSpan) {
              offCountSpan.textContent = offDays;
            } else {
              console.warn(`Warning: Off count span not found for employee: ${emp}`);
            }
          }
        }
      } else {
        console.error('API error when recalculating shift counts:', data.error);
      }
    })
    .catch(error => {
      console.error('Fetch error during recalculate_shift_counts:', error);
    });
  }
});
