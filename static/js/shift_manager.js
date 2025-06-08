document.addEventListener('DOMContentLoaded', () => {
  let selectedEmployees = [];
  const employeeBoxes = Array.from(document.querySelectorAll('.employee-box'));

  function getInitialFromName(name) {
    if (!name || name.length === 0) {
        return "";
    }
    return name.charAt(0).toUpperCase();
  }

  employeeBoxes.forEach(box => {
    box.addEventListener('click', e => {
      const empName = box.dataset.emp;
      if (e.ctrlKey || e.metaKey) {
        box.classList.toggle('emp-selected');
        if (box.classList.contains('emp-selected')) {
          if (!selectedEmployees.includes(empName)) {
            selectedEmployees.push(empName);
          }
        } else {
          selectedEmployees = selectedEmployees.filter(emp => emp !== empName);
        }
      } else {
        employeeBoxes.forEach(otherBox => {
          if (otherBox !== box) {
            otherBox.classList.remove('emp-selected');
          }
        });
        box.classList.add('emp-selected');
        selectedEmployees = [empName];
      }
    });

    box.addEventListener('dragstart', e => {
      const empName = box.dataset.emp;
      if (selectedEmployees.includes(empName) && selectedEmployees.length > 1) {
        e.dataTransfer.setData('text/plain', selectedEmployees.join(','));
      } else {
        // If not part of current multi-selection or only one selected, drag only this one
        // Ensure single selection if dragging an unselected item from the top list
        if (!selectedEmployees.includes(empName)) {
            employeeBoxes.forEach(otherBox => otherBox.classList.remove('emp-selected'));
            box.classList.add('emp-selected');
            selectedEmployees = [empName];
        } else if (selectedEmployees.length === 1 && selectedEmployees[0] !== empName) {
            // This case handles dragging a box that wasn't the primary selected one
            // (e.g. clicked A, then Ctrl+clicked B, then dragged A - B should be deselected)
            // However, the current click logic should already handle this by making A the sole selection.
            // For safety, we ensure only the dragged item is considered selected.
            employeeBoxes.forEach(otherBox => {
              if(otherBox !== box) otherBox.classList.remove('emp-selected');
            });
            selectedEmployees = [empName];
        }
        e.dataTransfer.setData('text/plain', empName);
      }
      e.dataTransfer.setData('text/from-cell', '');
      e.dataTransfer.effectAllowed = 'move';
    });
  });

  Array.from(document.querySelectorAll('.shift-cell')).forEach(cell => {
    const input = cell.querySelector('input');
    const list = cell.querySelector('.assignments');

    function addSpanEventListeners(span) {
      const empName = span.dataset.emp;
      if (!empName) {
        console.error("Span is missing data-emp attribute:", span);
        return;
      }
      span.draggable = true;
      span.addEventListener('dragstart', e => {
        e.dataTransfer.setData('text/plain', empName);
        e.dataTransfer.setData('text/from-cell', cell.dataset.date);
        e.dataTransfer.effectAllowed = 'move';
      });
      span.addEventListener('click', () => {
        let emps = input.value ? input.value.split(',') : [];
        const idx = emps.indexOf(empName);
        if (idx >= 0) {
          emps.splice(idx, 1);
          input.value = emps.join(',');
          span.remove();
          updateShiftCounts().then(() => {
            triggerShiftViolationCheck();
          }).catch(error => console.error("Error updating counts/violations after click removal:", error));
        }
      });
    }

    Array.from(list.querySelectorAll('.assigned')).forEach(s => {
        if(!s.dataset.emp && s.textContent) {
            const match = s.textContent.trim().match(/^[^(\s]*/);
            if (match) s.dataset.emp = match[0];
        }
        addSpanEventListeners(s);
    });

    function handleDrop(e) {
      e.preventDefault();
      const empNamesFromDropString = e.dataTransfer.getData('text/plain');
      if (!empNamesFromDropString) return;
      const droppedEmployeeNames = empNamesFromDropString.split(',');
      const originDate = e.dataTransfer.getData('text/from-cell');
      let empsInCell = input.value ? input.value.split(',') : [];

      droppedEmployeeNames.forEach(empName => {
        if (!empsInCell.includes(empName)) {
          empsInCell.push(empName);
          const newSpan = document.createElement('span');
          newSpan.className = 'assigned event-shift-item'; // Added event-shift-item for consistency
          newSpan.dataset.emp = empName;
          newSpan.textContent = getInitialFromName(empName); // Use helper to set initial
          // Add user-specific color class for the initial text
          newSpan.classList.add('initial-text-' + empName.toLowerCase().replace(/ /g, '_'));
          list.appendChild(newSpan);
          addSpanEventListeners(newSpan);
        }

        if (originDate && originDate !== cell.dataset.date) {
          const originCell = document.querySelector(`.shift-cell[data-date="${originDate}"]`);
          if (originCell) {
            const originInput = originCell.querySelector('input');
            const originList = originCell.querySelector('.assignments');
            let originEmps = originInput.value ? originInput.value.split(',') : [];
            const idx = originEmps.indexOf(empName);
            if (idx >= 0) {
              originEmps.splice(idx, 1);
              originInput.value = originEmps.join(',');
              originList.querySelectorAll('.assigned').forEach(s => {
                if (s.dataset.emp === empName) s.remove();
              });
            }
          }
        }
      });
      input.value = empsInCell.join(',');

      // Clear selection after drop
      selectedEmployees = [];
      employeeBoxes.forEach(box => box.classList.remove('emp-selected'));
      // Also clear selection from assigned spans if they were part of a drag
      // This is more complex as assigned spans are not in employeeBoxes array.
      // For now, focusing on clearing the top list selection.
      // A more robust solution might involve a global list of all draggable items.

      updateShiftCounts().then(() => {
        triggerShiftViolationCheck();
      }).catch(error => console.error("Error updating counts/violations after drop:", error));
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
    const currentMonthStr = statsSummaryCardBody.dataset.currentMonth;
    if (!currentMonthStr) {
      console.error('Error: data-current-month attribute not found.');
      return Promise.reject('data-current-month attribute not found');
    }
    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2);
      currentAssignments[dateKey] = input.value ? input.value.split(',').map(e=>e.trim()).filter(e=>e) : [];
    });
    return fetch('/calendario/api/shift_counts/recalculate', {
      method: 'POST', headers: { 'Content-Type': 'application/json', },
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
  }

  async function triggerShiftViolationCheck() {
    const statsSummaryCardBody = document.querySelector('.employee-stats-summary .card-body');
    const currentMonthStr = statsSummaryCardBody ? statsSummaryCardBody.dataset.currentMonth : null;
    if (!currentMonthStr) { console.error("Cannot check violations: current month not found."); return; }
    const currentAssignments = {};
    document.querySelectorAll('form input[type="hidden"][name^="d-"]').forEach(input => {
      const dateKey = input.name.substring(2);
      currentAssignments[dateKey] = input.value ? input.value.split(',').map(e=>e.trim()).filter(e=>e) : [];
    });
    const apiPayload = { assignments: currentAssignments, month: currentMonthStr };
    try {
      const response = await fetch('/calendario/api/check_shift_violations', {
        method: 'POST', headers: { 'Content-Type': 'application/json', },
        body: JSON.stringify(apiPayload)
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => null);
        throw new Error(errData?.error || response.statusText || `HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      if (data.success) {
        updateViolationsDisplay(data.violations);
        if (data.consecutive_work_info) {
            updateConsecutiveWorkDisplay(data.consecutive_work_info);
        }
      } else { console.error('API error checking shift violations:', data.error); }
    } catch (error) { console.error('Fetch error during triggerShiftViolationCheck:', error); }
  }

  function updateViolationsDisplay(violationsList) {
    document.querySelectorAll('.shift-cell .violation-icons').forEach(c => c.innerHTML = '');
    if (!violationsList || !Array.isArray(violationsList)) return;
    const ruleTypeToIcon = {
      "max_consecutive_days": { text: "連続", titlePrefix: "連続勤務超過" },
      "min_staff_per_day": { text: "人数", titlePrefix: "最低人数不足" },
      "forbidden_pair": { text: "禁止P", titlePrefix: "禁止ペア" },
      "required_pair": { text: "必須P", titlePrefix: "必須ペア不足" },
      "required_attribute_count": { text: "属性", titlePrefix: "属性人数不足" },
      "placeholder_violation_from_api": {text: "!", titlePrefix: "API警告"}
    };
    violationsList.forEach(violation => {
      const cell = document.querySelector(`.shift-cell[data-date="${violation.date}"]`);
      if (cell) {
        let iconsC = cell.querySelector('.violation-icons');
        if (!iconsC) { iconsC = document.createElement('div'); iconsC.className = 'violation-icons'; cell.appendChild(iconsC); }
        const iconEl = document.createElement('span');
        const iconInfo = ruleTypeToIcon[violation.rule_type] || {text: "?", titlePrefix: "不明ルール"};
        iconEl.className = `violation-icon type-${violation.rule_type}`; iconEl.textContent = iconInfo.text;
        iconEl.title = `${iconInfo.titlePrefix}: ${violation.description}`;
        iconEl.dataset.violationDetails = JSON.stringify(violation);

        iconEl.addEventListener('click', () => {
          let detailsObj;
          try {
            detailsObj = JSON.parse(iconEl.dataset.violationDetails);
          } catch (e) {
            console.error("Failed to parse violation details:", e, iconEl.dataset.violationDetails);
            alert("違反詳細の表示に失敗しました。");
            return;
          }

          const modalTitleEl = document.getElementById('violationDetailModalTitle');
          const modalBodyEl = document.getElementById('violationDetailModalBody');
          const modalElement = document.getElementById('violationDetailModal');

          if (modalTitleEl) modalTitleEl.textContent = `${iconInfo.titlePrefix} (${detailsObj.date})`;

          if (modalBodyEl) {
            // New structured HTML for modal body
            let bodyContent = `<p class="mb-2"><strong>概要:</strong> ${detailsObj.description || 'N/A'}</p>`;

            if (detailsObj.employee) {
                bodyContent += `<p class="mb-1"><strong>対象従業員:</strong> ${detailsObj.employee}</p>`;
            }
            if (detailsObj.employees && Array.isArray(detailsObj.employees) && detailsObj.employees.length > 0) {
                bodyContent += `<p class="mb-1"><strong>関連従業員:</strong> ${detailsObj.employees.join(', ')}</p>`;
            }
            if (detailsObj.attribute) {
                bodyContent += `<p class="mb-1"><strong>対象属性:</strong> ${detailsObj.attribute}</p>`;
            }

            if (detailsObj.details && typeof detailsObj.details === 'object' && Object.keys(detailsObj.details).length > 0) {
                bodyContent += `<p class="mt-3 mb-1"><strong>詳細情報:</strong></p><ul class="list-unstyled ps-3">`;
                for (const key in detailsObj.details) {
                    let displayKey = key;
                    if (key === "current_consecutive") displayKey = "現在の連勤日数";
                    else if (key === "max_allowed") displayKey = "最大許容日数";
                    else if (key === "current_staff") displayKey = "現在の人数";
                    else if (key === "min_required") displayKey = "最低必要人数";
                    else if (key === "pair") displayKey = "ペア";
                    else if (key === "missing_member") displayKey = "不足メンバー";
                    else if (key === "present_member") displayKey = "勤務中メンバー";
                    else if (key === "current_count") displayKey = "現在のカウント";
                    else if (key === "required_count") displayKey = "要求カウント";
                    else if (key === "date" && detailsObj.date) continue; // Already in title
                    else if (key === "employee" && detailsObj.employee) continue;
                    else if (key === "attribute" && detailsObj.attribute) continue;

                    bodyContent += `<li><strong>${displayKey}:</strong> ${detailsObj.details[key]}</li>`;
                }
                bodyContent += `</ul>`;
            }
            modalBodyEl.innerHTML = bodyContent;
          }

          if (modalElement && typeof bootstrap !== 'undefined' && bootstrap.Modal) {
            const modalInstance = bootstrap.Modal.getOrCreateInstance(modalElement);
            modalInstance.show();
          } else {
            console.error('Modal element #violationDetailModal not found or Bootstrap not loaded!');
            alert(`違反: ${detailsObj.description}\n詳細: ${JSON.stringify(detailsObj.details)}`);
          }
        });
        iconsC.appendChild(iconEl);
      }
    });
  }

  function updateConsecutiveWorkDisplay(consecutiveWorkInfo) {
    document.querySelectorAll('.shift-cell .assigned .consecutive-days-text').forEach(span => span.remove());
    if (!consecutiveWorkInfo) return;
    document.querySelectorAll('.shift-cell').forEach(cell => {
      const cellDate = cell.dataset.date;
      cell.querySelectorAll('.assignments .assigned').forEach(assignedSpan => {
        const empName = assignedSpan.dataset.emp;
        if (!empName) return;
        if (consecutiveWorkInfo[empName] && consecutiveWorkInfo[empName][cellDate]) {
          const count = consecutiveWorkInfo[empName][cellDate];
          let countSpan = assignedSpan.querySelector('.consecutive-days-text');
          if (!countSpan) {
            countSpan = document.createElement('span');
            countSpan.className = 'consecutive-days-text ms-1';
            countSpan.style.fontSize = '0.8em'; countSpan.style.color = '#555';
            assignedSpan.appendChild(countSpan);
          }
          countSpan.textContent = `(${count}日目)`;
        }
      });
    });
  }

  updateShiftCounts().then(() => {
    triggerShiftViolationCheck();
  }).catch(error => {
    console.error("Initial setup failed:", error);
    updateViolationsDisplay([]);
    updateConsecutiveWorkDisplay({});
  });

  const checkViolationsBtn = document.getElementById('checkViolationsBtn');
  if(checkViolationsBtn) {
    checkViolationsBtn.addEventListener('click', () => {
        updateShiftCounts().then(() => {
            triggerShiftViolationCheck();
        }).catch(error => {
            console.error("Manual check failed:", error);
            alert("ルールチェックの実行に失敗しました。詳細はコンソールを確認してください。");
        });
    });
  }
});
