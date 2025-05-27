// JavaScript helpers for shift_rules page

document.addEventListener('DOMContentLoaded', () => {
  function setupSingle(name) {
    const hidden = document.getElementById(name + '_hidden');
    const input = document.getElementById(name + '_input');
    const addBtn = document.getElementById(name + '_add');
    const list = document.getElementById(name + '_list');
    function render() {
      list.innerHTML = '';
      if (hidden.value) {
        const li = document.createElement('li');
        li.textContent = hidden.value;
        const del = document.createElement('button');
        del.type = 'button';
        del.textContent = '削除';
        del.addEventListener('click', () => {
          hidden.value = '';
          render();
        });
        li.appendChild(del);
        list.appendChild(li);
      }
    }
    addBtn.addEventListener('click', () => {
      if (input.value) {
        hidden.value = input.value;
        input.value = '';
        render();
      }
    });
    render();
  }

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

  setupSingle('max_consecutive_days');
  setupSingle('min_staff_per_day');
  setupPairList('forbidden_pairs', '#forbidden_a', '#forbidden_b');
  setupPairList('required_pairs', '#required_a', '#required_b');
  setupAttrList();
  setupReqAttrList();
});
