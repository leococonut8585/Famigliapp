document.addEventListener('DOMContentLoaded', () => {
  Array.from(document.querySelectorAll('.employee-box')).forEach(box => {
    box.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', box.dataset.emp);
      e.dataTransfer.setData('text/from-cell', ''); // No specific cell of origin for employee box
      e.dataTransfer.effectAllowed = 'move';
    });
  });

  Array.from(document.querySelectorAll('.shift-cell')).forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    function addSpan(span) {
      span.draggable = true;
      span.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', span.textContent);
        e.dataTransfer.setData('text/from-cell', cell.dataset.date); // This span is from this cell
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
          updateShiftCounts().then(() => { // Chain violation check
            triggerShiftViolationCheck();
          });
        }
      });
    }

    Array.from(list.querySelectorAll('.assigned')).forEach(addSpan);

    function handleDrop(e) {
      e.preventDefault();
      const emp = e.dataTransfer.getData('text/plain');
      if (!emp) return;
      
      const originDate = e.dataTransfer.getData('text/from-cell');

      // Add to target cell (this cell)
      let emps = input.value ? input.value.split(',') : [];
      if (!emps.includes(emp)) {
        emps.push(emp);
        input.value = emps.join(',');
        const span = document.createElement('span');
        span.className = 'assigned';
        span.textContent = emp;
        addSpan(span); // Make new span draggable and clickable
        list.appendChild(span);
      }
      
      // Remove from origin cell if it's a different cell
      if (originDate && originDate !== cell.dataset.date) {
        const originCell = document.querySelector(`.shift-cell[data-date="${originDate}"]`);
        if (originCell) {
          const originInput = originCell.querySelector('input');
          const originList = originCell.querySelector('.assignments');
          let originEmps = originInput.value ? originInput.value.split(',') : [];
          const idx = originEmps.indexOf(emp);
          if (idx >= 0) {
            originEmps.splice(idx, 1);
            originInput.value = originEmps.join(',');
            // Remove the specific span from the origin list
            originList.querySelectorAll('.assigned').forEach(s => {
              if (s.textContent === emp) s.remove();
            });
          }
        }
      }
      updateShiftCounts().then(() => { // Chain violation check
        triggerShiftViolationCheck();
      });
    }

    cell.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
    list.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }); // list also needs to be a drop target
    cell.addEventListener('drop', handleDrop);
    list.addEventListener('drop', handleDrop); // Allow dropping directly onto the list of assignments
  });

  function updateShiftCounts() { // Modified to return promise
    const statsSummaryDiv = document.querySelector('.employee-stats-summary');
    if (!statsSummaryDiv) {
      console.error('Error: Employee stats summary element not found.');
      return Promise.resolve(); // Return a resolved promise
    }
    const currentMonth = statsSummaryDiv.dataset.currentMonth;
    if (!currentMonth) {
      console.error('Error: data-current-month attribute not found on stats summary element.');
      return Promise.resolve();
    }

    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2); 
      const employees = input.value ? input.value.split(',').map(emp => emp.trim()).filter(emp => emp) : [];
      currentAssignments[dateKey] = employees;
    });

    // Return the fetch promise
    return fetch('/calendario/api/shift_counts/recalculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', },
      body: JSON.stringify({ month: currentMonth, assignments: currentAssignments })
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(errData => {
          throw new Error(errData.error || response.statusText || `HTTP error! status: ${response.status}`);
        }).catch(() => { throw new Error(response.statusText || `HTTP error! status: ${response.status}`); });
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        if (data.counts) {
          for (const [emp, workDays] of Object.entries(data.counts)) {
            const workCountSpan = document.querySelector(`.work-count[data-emp="${emp}"]`);
            if (workCountSpan) workCountSpan.textContent = workDays;
            else console.warn(`Warning: Work count span not found for employee: ${emp}`);
          }
        }
        if (data.off_counts) {
          for (const [emp, offDays] of Object.entries(data.off_counts)) {
            const offCountSpan = document.querySelector(`.off-count[data-emp="${emp}"]`);
            if (offCountSpan) offCountSpan.textContent = offDays;
            else console.warn(`Warning: Off count span not found for employee: ${emp}`);
          }
        }
      } else { console.error('API error when recalculating shift counts:', data.error); }
    })
    .catch(error => { console.error('Fetch error during recalculate_shift_counts:', error); });
  }

  async function triggerShiftViolationCheck() {
    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2);
      const employees = input.value ? input.value.split(',').map(emp => emp.trim()).filter(emp => emp) : [];
      currentAssignments[dateKey] = employees;
    });

    const apiPayload = { assignments: currentAssignments };

    try {
      const response = await fetch('/calendario/api/check_shift_violations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', },
        body: JSON.stringify(apiPayload)
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.error || response.statusText || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        updateViolationsDisplay(data.violations);
      } else {
        console.error('API error checking shift violations:', data.error);
      }
    } catch (error) {
      console.error('Fetch error during triggerShiftViolationCheck:', error);
    }
  }

  function updateViolationsDisplay(violationsList) {
    // Clear existing icons
    document.querySelectorAll('.shift-cell .violation-icons').forEach(container => {
      container.innerHTML = '';
    });

    if (!violationsList || !Array.isArray(violationsList)) return;

    const ruleTypeToIcon = {
      "max_consecutive_days": { text: "連続", titlePrefix: "連続勤務日数超過:" },
      "min_staff_per_day": { text: "人数", titlePrefix: "最低人数不足:" },
      "forbidden_pair": { text: "禁止ペア", titlePrefix: "禁止ペア:" },
      "required_pair": { text: "必須ペア", titlePrefix: "必須ペア不足:" },
      "required_attribute_count": { text: "属性", titlePrefix: "属性人数不足:" },
      "placeholder_violation": { text: "!", titlePrefix: "テスト警告:"} // For placeholder
    };

    violationsList.forEach(violation => {
      const cell = document.querySelector(`.shift-cell[data-date="${violation.date}"]`);
      if (cell) {
        let iconsContainer = cell.querySelector('.violation-icons');
        if (!iconsContainer) { // Create if not exists (should be added in HTML template later)
          iconsContainer = document.createElement('div');
          iconsContainer.className = 'violation-icons';
          // Find a suitable place to append, e.g., after assignments list or at the top of cell content
          const assignmentsList = cell.querySelector('.assignments');
          if(assignmentsList && assignmentsList.parentNode) {
            assignmentsList.parentNode.insertBefore(iconsContainer, assignmentsList.nextSibling);
          } else {
             cell.appendChild(iconsContainer); // Fallback
          }
        }
        
        const iconEl = document.createElement('span');
        const iconInfo = ruleTypeToIcon[violation.rule_type] || {text: "?", titlePrefix: "不明なルール:"};
        
        iconEl.className = `violation-icon type-${violation.rule_type}`;
        iconEl.textContent = iconInfo.text;
        iconEl.title = `${iconInfo.titlePrefix} ${violation.description}`;
        iconEl.dataset.violationDetails = JSON.stringify(violation);

        iconEl.addEventListener('click', () => {
          const details = JSON.parse(iconEl.dataset.violationDetails);
          // Populate and show modal (assuming Bootstrap modal structure)
          const modalTitleEl = document.getElementById('violationDetailModalTitle');
          const modalBodyEl = document.getElementById('violationDetailModalBody');
          
          if (modalTitleEl) modalTitleEl.textContent = `違反詳細: ${iconInfo.titlePrefix.slice(0,-1)} (${details.date})`;
          if (modalBodyEl) {
            let detailsHtml = `<p><strong>説明:</strong> ${details.description}</p>`;
            if(details.employee) detailsHtml += `<p><strong>従業員:</strong> ${details.employee}</p>`;
            if(details.employees) detailsHtml += `<p><strong>関連従業員:</strong> ${details.employees.join(', ')}</p>`;
            if(details.attribute) detailsHtml += `<p><strong>属性:</strong> ${details.attribute}</p>`;
            if(details.details) { // Generic details object
                detailsHtml += `<p><strong>詳細情報:</strong></p><ul>`;
                for(const [key, value] of Object.entries(details.details)) {
                    detailsHtml += `<li><strong>${key}:</strong> ${value}</li>`;
                }
                detailsHtml += `</ul>`;
            }
            modalBodyEl.innerHTML = detailsHtml;
          }
          // Attempt to show modal if Bootstrap is used and modal is set up
          const modal = document.getElementById('violationDetailModal');
          if (modal && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const bsModal = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
            bsModal.show();
          } else {
            alert(`違反: ${details.description}\n詳細: ${JSON.stringify(details.details)}`); // Fallback alert
          }
        });
        iconsContainer.appendChild(iconEl);
      }
    });
  }
  
  // Initial check on page load
  updateShiftCounts().then(() => {
    triggerShiftViolationCheck();
  });
});
