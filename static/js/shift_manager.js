document.addEventListener('DOMContentLoaded', () => {
  Array.from(document.querySelectorAll('.employee-box')).forEach(box => {
    box.addEventListener('dragstart', e => {
      e.dataTransfer.setData('text/plain', box.dataset.emp);
      e.dataTransfer.setData('text/from-cell', ''); 
      e.dataTransfer.effectAllowed = 'move';
    });
  });

  Array.from(document.querySelectorAll('.shift-cell')).forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    function addSpanEventListeners(span) { // Renamed original addSpan to addSpanEventListeners
      const empName = span.dataset.emp; // Assumes/Ensures data-emp is set
      if (!empName) {
        console.error("Span is missing data-emp attribute:", span);
        return;
      }

      span.draggable = true;
      span.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', empName); // Use empName from data-emp
        e.dataTransfer.setData('text/from-cell', cell.dataset.date);
        e.dataTransfer.effectAllowed = 'move';
      });
      span.addEventListener('click', () => {
        let emps = input.value ? input.value.split(',') : [];
        const idx = emps.indexOf(empName); // Use empName from data-emp
        if (idx >= 0) {
          emps.splice(idx, 1);
          input.value = emps.join(',');
          span.remove();
          updateShiftCounts().then(() => { 
            triggerShiftViolationCheck();
          });
        }
      });
    }
    
    // Initial setup for existing spans from HTML (which should have data-emp)
    Array.from(list.querySelectorAll('.assigned')).forEach(s => {
        if(!s.dataset.emp && s.textContent) s.dataset.emp = s.textContent.trim().match(/^[^(\s]*/)[0]; // Fallback if data-emp not set
        addSpanEventListeners(s);
    });


    function handleDrop(e) {
      e.preventDefault();
      const empNameFromDrop = e.dataTransfer.getData('text/plain');
      if (!empNameFromDrop) return;
      
      const originDate = e.dataTransfer.getData('text/from-cell');

      let emps = input.value ? input.value.split(',') : [];
      if (!emps.includes(empNameFromDrop)) {
        emps.push(empNameFromDrop);
        input.value = emps.join(',');
        const newSpan = document.createElement('span');
        newSpan.className = 'assigned';
        newSpan.dataset.emp = empNameFromDrop; // Set data-emp
        newSpan.textContent = empNameFromDrop; // Set base text content
        // The consecutive day count will be added by updateConsecutiveWorkDisplay
        list.appendChild(newSpan);
        addSpanEventListeners(newSpan); // Add listeners to new span
      }
      
      if (originDate && originDate !== cell.dataset.date) {
        const originCell = document.querySelector(`.shift-cell[data-date="${originDate}"]`);
        if (originCell) {
          const originInput = originCell.querySelector('input');
          const originList = originCell.querySelector('.assignments');
          let originEmps = originInput.value ? originInput.value.split(',') : [];
          const idx = originEmps.indexOf(empNameFromDrop);
          if (idx >= 0) {
            originEmps.splice(idx, 1);
            originInput.value = originEmps.join(',');
            originList.querySelectorAll('.assigned').forEach(s => {
              if (s.dataset.emp === empNameFromDrop) s.remove(); // Check data-emp
            });
          }
        }
      }
      updateShiftCounts().then(() => { 
        triggerShiftViolationCheck();
      });
    }

    cell.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
    list.addEventListener('dragover', e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; });
    cell.addEventListener('drop', handleDrop);
    list.addEventListener('drop', handleDrop);
  });

  function updateShiftCounts() {
    const statsSummaryCardBody = document.querySelector('.employee-stats-summary .card-body');
    if (!statsSummaryCardBody) {
      console.error('Error: Stats summary card body element not found.');
      return Promise.reject('Stats summary card body not found');
    }
    const currentMonthStr = statsSummaryCardBody.dataset.currentMonth; // Get YYYY-MM
    if (!currentMonthStr) {
      console.error('Error: data-current-month attribute not found.');
      return Promise.reject('data-current-month attribute not found');
    }

    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2); 
      const employees = input.value ? input.value.split(',').map(emp => emp.trim()).filter(emp => emp) : [];
      currentAssignments[dateKey] = employees;
    });

    return fetch('/calendario/api/shift_counts/recalculate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', },
      body: JSON.stringify({ month: currentMonthStr, assignments: currentAssignments })
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(errData => { throw new Error(errData.error || response.statusText); });
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        for (const [emp, workDays] of Object.entries(data.counts || {})) {
            const el = document.querySelector(`.work-count[data-emp="${emp}"]`); if (el) el.textContent = workDays;
        }
        for (const [emp, offDays] of Object.entries(data.off_counts || {})) {
            const el = document.querySelector(`.off-count[data-emp="${emp}"]`); if (el) el.textContent = offDays;
        }
      } else { console.error('API error recalculating counts:', data.error); }
    })
    .catch(error => { console.error('Fetch error during recalculate_shift_counts:', error); });
  }

  async function triggerShiftViolationCheck() {
    const statsSummaryCardBody = document.querySelector('.employee-stats-summary .card-body');
    const currentMonthStr = statsSummaryCardBody ? statsSummaryCardBody.dataset.currentMonth : null;
    if (!currentMonthStr) {
        console.error("Cannot trigger violation check: current month not found.");
        return;
    }

    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2);
      const employees = input.value ? input.value.split(',').map(emp => emp.trim()).filter(emp => emp) : [];
      currentAssignments[dateKey] = employees;
    });

    const apiPayload = { 
        assignments: currentAssignments,
        month: currentMonthStr // Added month to payload
    };

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
        if (data.consecutive_work_info) { // Process new consecutive day info
            updateConsecutiveWorkDisplay(data.consecutive_work_info);
        }
      } else {
        console.error('API error checking shift violations:', data.error);
      }
    } catch (error) {
      console.error('Fetch error during triggerShiftViolationCheck:', error);
    }
  }

  function updateViolationsDisplay(violationsList) {
    document.querySelectorAll('.shift-cell .violation-icons').forEach(c => c.innerHTML = '');
    if (!violationsList || !Array.isArray(violationsList)) return;
    const ruleTypeToIcon = {
      "max_consecutive_days": { text: "連続", titlePrefix: "連続勤務超過:" },
      "min_staff_per_day": { text: "人数", titlePrefix: "最低人数不足:" },
      "forbidden_pair": { text: "禁止P", titlePrefix: "禁止ペア:" },
      "required_pair": { text: "必須P", titlePrefix: "必須ペア不足:" },
      "required_attribute_count": { text: "属性", titlePrefix: "属性人数不足:" },
      "placeholder_violation_from_api": {text: "!", titlePrefix: "API警告:"} // Matching placeholder
    };
    violationsList.forEach(v => {
      const cell = document.querySelector(`.shift-cell[data-date="${v.date}"]`);
      if (cell) {
        let iconsC = cell.querySelector('.violation-icons');
        if (!iconsC) { iconsC = document.createElement('div'); iconsC.className = 'violation-icons'; cell.appendChild(iconsC); }
        const iconEl = document.createElement('span');
        const iconInfo = ruleTypeToIcon[v.rule_type] || {text: "?", titlePrefix: "不明ルール:"};
        iconEl.className = `violation-icon type-${v.rule_type}`; iconEl.textContent = iconInfo.text;
        iconEl.title = `${iconInfo.titlePrefix} ${v.description}`; iconEl.dataset.violationDetails = JSON.stringify(v);
        iconEl.addEventListener('click', () => { /* ... modal logic ... */ });
        iconsC.appendChild(iconEl);
      }
    });
  }

  function updateConsecutiveWorkDisplay(consecutiveWorkInfo) {
    // Clear existing consecutive day counts
    document.querySelectorAll('.shift-cell .assigned .consecutive-days-text').forEach(span => span.remove());

    if (!consecutiveWorkInfo) return;

    document.querySelectorAll('.shift-cell').forEach(cell => {
      const cellDate = cell.dataset.date;
      cell.querySelectorAll('.assignments .assigned').forEach(assignedSpan => {
        const empName = assignedSpan.dataset.emp; // Assumes data-emp is set
        if (!empName) return;

        if (consecutiveWorkInfo[empName] && consecutiveWorkInfo[empName][cellDate]) {
          const count = consecutiveWorkInfo[empName][cellDate];
          let countSpan = assignedSpan.querySelector('.consecutive-days-text');
          if (!countSpan) {
            countSpan = document.createElement('span');
            countSpan.className = 'consecutive-days-text ms-1'; // Use new class
            // Style directly or via CSS class
            countSpan.style.fontSize = '0.8em';
            countSpan.style.color = '#555'; // Darker gray for better visibility
            assignedSpan.appendChild(countSpan);
          }
          countSpan.textContent = `(${count}日目)`;
        }
      });
    });
  }
  
  // Initial check on page load
  updateShiftCounts().then(() => {
    triggerShiftViolationCheck();
  }).catch(error => {
    console.error("Initial setup failed:", error);
    // Optionally, trigger a baseline display if counts/violations fail to load
    updateViolationsDisplay([]); // Clear violations display
    updateConsecutiveWorkDisplay({}); // Clear consecutive days display
  });

  // Manual check button
  const checkViolationsBtn = document.getElementById('checkViolationsBtn');
  if(checkViolationsBtn) {
    checkViolationsBtn.addEventListener('click', () => {
        updateShiftCounts().then(() => { // Ensure counts are up-to-date with DOM before checking
            triggerShiftViolationCheck();
        }).catch(error => {
            console.error("Manual check failed:", error);
            alert("ルールチェックの実行に失敗しました。詳細はコンソールを確認してください。");
        });
    });
  }
});
