// JavaScript helpers for shift_rules page

document.addEventListener('DOMContentLoaded', () => {
  // Existing setup functions (setupPairList, setupAttrList, setupReqAttrList, etc.)
  // ... (Keep all existing JavaScript code from the previous read_files output here) ...

  function setupPairList(name, selectA, selectB) {
    const hidden = document.getElementById(name + '_hidden');
    const listEl = document.getElementById(name + '_list');
    const addBtn = document.getElementById(name + '_add');
    const pairs = hidden.value ? hidden.value.split(',').filter(s=>s).map(s => s.split('-')) : [];
    function updateHidden() {
      hidden.value = pairs.map(p => p.join('-')).join(',');
    }
    function render() {
      listEl.innerHTML = '';
      pairs.forEach((p, idx) => {
        const li = document.createElement('li');
        li.textContent = p[0] + ' - ' + p[1];
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '削除';
        del.classList.add('btn', 'btn-sm', 'btn-danger', 'ms-2');
        del.addEventListener('click', () => {
          pairs.splice(idx, 1);
          updateHidden();
          render();
        });
        li.appendChild(del);
        listEl.appendChild(li);
      });
    }
    addBtn.addEventListener('click', () => {
      const a = document.querySelector(selectA).value;
      const b = document.querySelector(selectB).value;
      if (a && b) {
        if (a === b) {
          alert('同じ担当者をペアに設定することはできません。');
          return;
        }
        // Check for duplicate pairs (A-B or B-A)
        const exists = pairs.some(p => (p[0] === a && p[1] === b) || (p[0] === b && p[1] === a));
        if (exists) {
          alert('そのペアは既に追加されています。');
          return;
        }
        pairs.push([a, b]);
        updateHidden();
        render();
      }
    });
    render();
  }

  function setupAttrList() {
    const hidden = document.getElementById('employee_attributes_hidden');
    const listEl = document.getElementById('attr_list');
    const addBtn = document.getElementById('attr_add');
    let data = {};
    if (hidden.value) {
      hidden.value.split(',').forEach(item => {
        if (!item) return;
        const [emp, attrs] = item.split(':');
        if (emp) {
          data[emp] = attrs ? attrs.split('|') : [];
        }
      });
    }
    function updateHidden() {
      const parts = [];
      Object.keys(data).forEach(emp => {
        if (data[emp].length) {
          parts.push(emp + ':' + data[emp].join('|'));
        }
      });
      hidden.value = parts.join(',');
    }
    function render() {
      listEl.innerHTML = '';
      Object.keys(data).forEach(emp => {
        const li = document.createElement('li');
        li.textContent = emp + ': ' + data[emp].join('|');
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '削除';
        del.classList.add('btn', 'btn-sm', 'btn-danger', 'ms-2');
        del.addEventListener('click', () => {
          delete data[emp];
          updateHidden();
          render();
        });
        li.appendChild(del);
        listEl.appendChild(li);
      });
    }
    addBtn.addEventListener('click', () => {
      const emp = document.getElementById('attr_employee').value;
      const attrs = Array.from(document.querySelectorAll('.attr_cb:checked')).map(cb => cb.value);
      if (emp) { // Allow adding employee with no attributes (to clear them)
        data[emp] = attrs; // Assign new list of attributes (can be empty)
        document.querySelectorAll('.attr_cb').forEach(cb => cb.checked = false);
        updateHidden();
        render();
      }
    });
    render();
  }

  function setupReqAttrList() {
    const hidden = document.getElementById('required_attributes_hidden');
    const listEl = document.getElementById('req_attr_list');
    const addBtn = document.getElementById('req_attr_add');
    let data = {};
    if (hidden.value) {
      hidden.value.split(',').forEach(item => {
        if (!item.includes(':')) return;
        const [attr, num] = item.split(':');
        const n = parseInt(num, 10);
        if (attr) data[attr] = isNaN(n) ? 0 : n;
      });
    }
    function updateHidden() {
      hidden.value = Object.entries(data).map(([a,n]) => a + ':' + n).join(',');
    }
    function render() {
      listEl.innerHTML = '';
      Object.keys(data).forEach(attr => {
        const li = document.createElement('li');
        li.textContent = attr + ': ' + data[attr];
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '削除';
        del.classList.add('btn', 'btn-sm', 'btn-danger', 'ms-2');
        del.addEventListener('click', () => {
          delete data[attr];
          updateHidden();
          render();
        });
        li.appendChild(del);
        listEl.appendChild(li);
      });
    }
    addBtn.addEventListener('click', () => {
      const attr = document.getElementById('req_attr_attr').value;
      const numInput = document.getElementById('req_attr_num');
      const num = parseInt(numInput.value, 10);
      if (attr && !isNaN(num) && num >= 0) {
        data[attr] = num;
        numInput.value = ''; // Clear input after adding
        updateHidden();
        render();
      } else if (!attr) {
        alert('属性を選択してください。');
      } else {
        alert('有効な人数（0以上）を入力してください。');
      }
    });
    render();
  }

  let currentDefinedAttributes = Array.isArray(window.initialShiftAttributes) ? [...window.initialShiftAttributes] : ["Dog", "Lady", "Man", "Kaji", "Massage"]; // Fallback, ensure it's a copy

  const definedAttributesInputEl = document.getElementById('new_defined_attribute_input');
  const definedAttributesAddBtnEl = document.getElementById('add_defined_attribute_button');
  const definedAttributesListDisplayEl = document.getElementById('defined_attributes_list_display');
  const definedAttributesJsonHiddenEl = document.getElementById('defined_attributes_json_str');

  const employeeAttributesCheckboxGroupEl = document.getElementById('employee_attributes_checkbox_group');
  const reqAttrAttrSelectEl = document.getElementById('req_attr_attr');

  function updateHiddenDefinedAttributes() {
    if (definedAttributesJsonHiddenEl) {
      definedAttributesJsonHiddenEl.value = JSON.stringify(currentDefinedAttributes);
    }
  }

  function renderAttributeDependentUI() {
    if (employeeAttributesCheckboxGroupEl) {
      employeeAttributesCheckboxGroupEl.innerHTML = '';
      if (currentDefinedAttributes.length === 0) {
        employeeAttributesCheckboxGroupEl.innerHTML = '<small class="text-muted">利用可能な属性はありません。まず「属性名の管理」で属性を追加してください。</small>';
      } else {
        currentDefinedAttributes.forEach(attr => {
          const div = document.createElement('div'); // Use div for better structure
          div.classList.add('form-check', 'form-check-inline');
          const checkbox = document.createElement('input');
          checkbox.type = 'checkbox';
          checkbox.className = 'attr_cb form-check-input';
          checkbox.value = attr;
          checkbox.id = `attr_cb_${attr}`; // Unique ID
          const label = document.createElement('label');
          label.className = 'form-check-label';
          label.setAttribute('for', `attr_cb_${attr}`);
          label.textContent = attr;
          div.appendChild(checkbox);
          div.appendChild(label);
          employeeAttributesCheckboxGroupEl.appendChild(div);
        });
      }
    }

    if (reqAttrAttrSelectEl) {
      reqAttrAttrSelectEl.innerHTML = '';
      if (currentDefinedAttributes.length === 0) {
          const option = document.createElement('option');
          option.value = "";
          option.textContent = "属性なし";
          reqAttrAttrSelectEl.appendChild(option);
      } else {
        currentDefinedAttributes.forEach(attr => {
          const option = document.createElement('option');
          option.value = attr;
          option.textContent = attr;
          reqAttrAttrSelectEl.appendChild(option);
        });
      }
    }
  }
  
  function renderDefinedAttributesList() {
    if (definedAttributesListDisplayEl) {
      definedAttributesListDisplayEl.innerHTML = '';
      currentDefinedAttributes.forEach((attr, index) => {
        const li = document.createElement('li');
        li.textContent = attr + ' ';
        const deleteBtn = document.createElement('button');
        deleteBtn.type = 'button';
        deleteBtn.textContent = '削除';
        deleteBtn.classList.add('btn', 'btn-sm', 'btn-danger', 'ms-1');
        deleteBtn.addEventListener('click', () => {
          currentDefinedAttributes.splice(index, 1);
          renderDefinedAttributesList();
          renderAttributeDependentUI();
          updateHiddenDefinedAttributes();
        });
        li.appendChild(deleteBtn);
        definedAttributesListDisplayEl.appendChild(li);
      });
    }
  }

  if (definedAttributesAddBtnEl) {
    definedAttributesAddBtnEl.addEventListener('click', () => {
      const newAttr = definedAttributesInputEl.value.trim();
      if (newAttr && !currentDefinedAttributes.includes(newAttr)) {
        currentDefinedAttributes.push(newAttr);
        definedAttributesInputEl.value = '';
        renderDefinedAttributesList();
        renderAttributeDependentUI();
        updateHiddenDefinedAttributes();
      } else if (!newAttr) {
        alert('属性名を入力してください。');
      } else {
        alert('その属性名は既に追加されています。');
      }
    });
  }

  // Initial setup for existing features
  renderDefinedAttributesList();
  renderAttributeDependentUI();
  updateHiddenDefinedAttributes();

  setupPairList('forbidden_pairs', '#forbidden_a', '#forbidden_b');
  setupPairList('required_pairs', '#required_a', '#required_b');
  setupAttrList();
  setupReqAttrList();

  // --- Specialized Requirements Logic ---
  const specializedRequirementsHiddenInput = document.getElementById('specialized_requirements_json_str');
  const categorySelect = document.getElementById('specialized_category_select');
  const employeeSelect = document.getElementById('specialized_employee_select');
  const addSpecializedBtn = document.getElementById('add_specialized_requirement_button');
  const specializedListDisplay = document.getElementById('specialized_requirements_list_display');
  const currentSpecializedSummaryDisplay = document.getElementById('current_specialized_requirements_display_summary');

  let specialized_requirements = {}; // { "category": ["emp1", "emp2"], ... }

  function renderSpecializedRequirementsDisplay() {
    specializedListDisplay.innerHTML = '';
    currentSpecializedSummaryDisplay.innerHTML = '';

    for (const category in specialized_requirements) {
      if (specialized_requirements[category].length > 0) {
        // Interactive list item
        const interactiveLi = document.createElement('li');
        interactiveLi.classList.add('mb-2');
        let interactiveText = `${category}: ${specialized_requirements[category].join(', ')} `;
        interactiveLi.appendChild(document.createTextNode(interactiveText));

        specialized_requirements[category].forEach(employee => {
          const removeBtn = document.createElement('button');
          removeBtn.type = 'button';
          removeBtn.textContent = `${employee}削除`;
          removeBtn.classList.add('btn', 'btn-sm', 'btn-outline-danger', 'ms-1', 'remove-specialized-btn');
          removeBtn.dataset.category = category;
          removeBtn.dataset.employee = employee;
          interactiveLi.appendChild(removeBtn);
        });
        specializedListDisplay.appendChild(interactiveLi);

        // Summary list item
        const summaryLi = document.createElement('li');
        summaryLi.textContent = `${category}: ${specialized_requirements[category].join(', ')}`;
        currentSpecializedSummaryDisplay.appendChild(summaryLi);
      }
    }
    // Update the hidden input field
    specializedRequirementsHiddenInput.value = JSON.stringify(specialized_requirements);
  }

  function loadInitialSpecializedRequirements() {
    // Assuming window.initialShiftRules is populated from the server, similar to window.initialShiftAttributes
    if (window.initialShiftRules && window.initialShiftRules.specialized_requirements) {
      const loadedReqs = window.initialShiftRules.specialized_requirements;
      // Basic validation: ensure it's an object
      if (typeof loadedReqs === 'object' && loadedReqs !== null) {
         // Ensure all categories have arrays as values
        for (const category in loadedReqs) {
            if (Array.isArray(loadedReqs[category])) {
                specialized_requirements[category] = [...new Set(loadedReqs[category])]; // Ensure unique employees
            } else {
                console.warn(`Invalid format for specialized_requirements category "${category}". Expected array.`);
                specialized_requirements[category] = [];
            }
        }
      } else {
          console.warn("window.initialShiftRules.specialized_requirements is not a valid object.");
      }
    }
    renderSpecializedRequirementsDisplay();
  }

  addSpecializedBtn.addEventListener('click', () => {
    const category = categorySelect.value;
    const employee = employeeSelect.value;

    if (!category || !employee) {
      alert('ジャンルと担当者の両方を選択してください。');
      return;
    }

    if (!specialized_requirements[category]) {
      specialized_requirements[category] = [];
    }

    if (!specialized_requirements[category].includes(employee)) {
      specialized_requirements[category].push(employee);
      // specialized_requirements[category].sort(); // Optional: sort employee list
      renderSpecializedRequirementsDisplay();
    } else {
      alert(`「${employee}」は既に「${category}」ジャンルに追加されています。`);
    }
  });

  specializedListDisplay.addEventListener('click', function(e) {
    if (e.target.classList.contains('remove-specialized-btn')) {
      const category = e.target.dataset.category;
      const employee = e.target.dataset.employee;

      if (specialized_requirements[category] && specialized_requirements[category].includes(employee)) {
        specialized_requirements[category] = specialized_requirements[category].filter(emp => emp !== employee);
        if (specialized_requirements[category].length === 0) {
          delete specialized_requirements[category]; // Remove category if no employees are left
        }
        renderSpecializedRequirementsDisplay();
      }
    }
  });

  // Load initial specialized requirements on page load
  loadInitialSpecializedRequirements();

  // Ensure the main form submission updates all hidden fields if not already handled
  // The current structure seems to update hidden fields on each modification,
  // so an explicit form submit listener here for THIS specific data might be redundant
  // if specializedRequirementsHiddenInput.value is always kept up-to-date.
  // However, ensuring defined_attributes_json_str is set on submit is good practice.
  const mainForm = document.getElementById('rules-form');
  if (mainForm) {
    mainForm.addEventListener('submit', () => {
      updateHiddenDefinedAttributes(); // Ensure this is up-to-date
      // specializedRequirementsHiddenInput is already updated by renderSpecializedRequirementsDisplay
    });
  }

});
