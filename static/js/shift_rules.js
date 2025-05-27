// JavaScript helpers for shift_rules page

document.addEventListener('DOMContentLoaded', () => {
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
        li.textContent = emp + ':' + data[emp].join('|');
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '削除';
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
      if (emp && attrs.length) {
        data[emp] = attrs;
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
      const num = parseInt(document.getElementById('req_attr_num').value, 10);
      if (attr && !isNaN(num)) {
        data[attr] = num;
        document.getElementById('req_attr_num').value = '';
        updateHidden();
        render();
      }
    });
    render();
  }

  // Initialize currentDefinedAttributes from a global variable set by the template
  // The template should include: <script>window.initialShiftAttributes = {{ attributes|tojson|safe }};</script>
  let currentDefinedAttributes = Array.isArray(window.initialShiftAttributes) ? window.initialShiftAttributes : ["Dog", "Lady", "Man", "Kaji", "Massage"]; // Fallback

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
    // Update checkboxes for Employee Attributes
    if (employeeAttributesCheckboxGroupEl) {
      employeeAttributesCheckboxGroupEl.innerHTML = ''; // Clear existing
      currentDefinedAttributes.forEach(attr => {
        const label = document.createElement('label');
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'attr_cb';
        checkbox.value = attr;
        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(' ' + attr));
        employeeAttributesCheckboxGroupEl.appendChild(label);
        employeeAttributesCheckboxGroupEl.appendChild(document.createTextNode(' ')); // For spacing
      });
    }

    // Update select options for Required Attributes per Day
    if (reqAttrAttrSelectEl) {
      reqAttrAttrSelectEl.innerHTML = ''; // Clear existing
      currentDefinedAttributes.forEach(attr => {
        const option = document.createElement('option');
        option.value = attr;
        option.textContent = attr;
        reqAttrAttrSelectEl.appendChild(option);
      });
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
        deleteBtn.addEventListener('click', () => {
          currentDefinedAttributes.splice(index, 1);
          renderDefinedAttributesList(); // Re-render this list
          updateAttributeDependentUI(); // Re-render dependent UI
          updateHiddenDefinedAttributes(); // Update hidden field for form submission
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
        updateAttributeDependentUI();
        updateHiddenDefinedAttributes();
      } else if (!newAttr) {
        alert('属性名を入力してください。');
      } else {
        alert('その属性名は既に追加されています。');
      }
    });
  }

  // Initial setup
  renderDefinedAttributesList();
  updateAttributeDependentUI();
  updateHiddenDefinedAttributes(); // Ensure hidden field is populated on load

  setupPairList('forbidden_pairs', '#forbidden_a', '#forbidden_b');
  setupPairList('required_pairs', '#required_a', '#required_b');
  setupAttrList(); // Should now use dynamically generated checkboxes
  setupReqAttrList(); // Should now use dynamically generated select options
});
