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
            // Extract name if only textContent is available (e.g. "empName (X日目)")
            const match = s.textContent.trim().match(/^[^(\s]*/);
            if (match) s.dataset.emp = match[0];
        }
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
        newSpan.dataset.emp = empNameFromDrop;
        newSpan.textContent = empNameFromDrop;
        list.appendChild(newSpan);
        addSpanEventListeners(newSpan);
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
              if (s.dataset.emp === empNameFromDrop) s.remove();
            });
          }
        }
      }
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
    // No catch here, let the caller chain catch if needed or handle final success/failure
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
        iconEl.title = `${iconInfo.titlePrefix}: ${violation.description}`; // Use full description for title
        iconEl.dataset.violationDetails = JSON.stringify(violation); // Store full object

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
            let detailsHtml = `<p><strong>説明:</strong> ${detailsObj.description || 'N/A'}</p>`;
            if(detailsObj.employee) detailsHtml += `<p><strong>従業員:</strong> ${detailsObj.employee}</p>`;
            if(detailsObj.employees && Array.isArray(detailsObj.employees)) detailsHtml += `<p><strong>関連従業員:</strong> ${detailsObj.employees.join(', ')}</p>`;
            if(detailsObj.attribute) detailsHtml += `<p><strong>属性:</strong> ${detailsObj.attribute}</p>`;

            if(detailsObj.details && typeof detailsObj.details === 'object' && Object.keys(detailsObj.details).length > 0) {
                detailsHtml += `<p><strong>詳細情報:</strong></p><ul>`;
                for (const [key, value] of Object.entries(detailsObj.details)) {
                    detailsHtml += `<li><strong>${key}:</strong> ${value}</li>`;
                }
                detailsHtml += `</ul>`;
            } else {
                detailsHtml += `<p>追加の詳細情報はありません。</p>`;
            }
            modalBodyEl.innerHTML = detailsHtml;
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
