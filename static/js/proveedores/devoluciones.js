/* Interacciones y DataTables para Devoluciones (Clientes y Proveedores) */
(function() {
  if (window.jQuery && jQuery.fn.dataTable) {
    jQuery.fn.dataTable.ext.errMode = 'none';
  }

  // Select con buscador (clase .dev-searchable)
  function initSearchableSelects() {
    document.querySelectorAll('select.dev-searchable').forEach(function(sel) {
      if (sel.dataset.ssReady) return;
      sel.dataset.ssReady = '1';
      sel.tabIndex = -1;

      const wrap = document.createElement('div');
      wrap.className = 'dev-ss';
      sel.parentNode.insertBefore(wrap, sel);
      wrap.appendChild(sel);

      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'dev-ss__input';
      input.autocomplete = 'off';
      input.placeholder = sel.dataset.placeholder || 'Buscar...';
      const list = document.createElement('ul');
      list.className = 'dev-ss__list';
      wrap.append(input, list);

      const options = [...sel.options].filter(function(o) { return o.value; });
      let active = -1;

      function norm(t) { return t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); }
      function close() { wrap.classList.remove('is-open'); active = -1; }
      function choose(opt) {
        sel.value = opt.value;
        input.value = opt.textContent.trim();
        input.classList.remove('is-invalid');
        sel.classList.remove('is-invalid');
        sel.dispatchEvent(new Event('change', { bubbles: true }));
        close();
      }
      function render() {
        const q = norm(input.value.trim());
        list.innerHTML = '';
        const found = options.filter(function(o) { return norm(o.textContent).indexOf(q) !== -1; });
        found.forEach(function(o) {
          const li = document.createElement('li');
          li.className = 'dev-ss__item';
          li.textContent = o.textContent.trim();
          li.addEventListener('mousedown', function(e) { e.preventDefault(); choose(o); });
          list.appendChild(li);
        });
        if (!found.length) {
          const li = document.createElement('li');
          li.className = 'dev-ss__empty';
          li.textContent = 'Sin resultados';
          list.appendChild(li);
        }
        active = -1;
        wrap.classList.add('is-open');
      }
      function move(dir) {
        const items = [...list.querySelectorAll('.dev-ss__item')];
        if (!items.length) return;
        active = (active + dir + items.length) % items.length;
        items.forEach(function(it, i) { it.classList.toggle('is-active', i === active); });
        items[active].scrollIntoView({ block: 'nearest' });
      }

      input.addEventListener('focus', function() { input.select(); render(); });
      input.addEventListener('input', function() { sel.value = ''; render(); });
      input.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
        else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
        else if (e.key === 'Enter') {
          const items = list.querySelectorAll('.dev-ss__item');
          if (wrap.classList.contains('is-open') && items.length) {
            e.preventDefault();
            items[active >= 0 ? active : 0].dispatchEvent(new MouseEvent('mousedown'));
          }
        } else if (e.key === 'Escape') { close(); }
      });
      input.addEventListener('blur', function() {
        close();
        const cur = options.find(function(o) { return o.value === sel.value; });
        input.value = cur ? cur.textContent.trim() : '';
      });

    });
  }

  function initDevolucionesPage() {
    initSearchableSelects();
    // 1. Lógica del formulario de pasos (si existe)
    const form = document.getElementById('formDevoluciones');
    if (form) {
      const productChecks = [...form.querySelectorAll('.dev-product-check')];
      productChecks.forEach((check) => {
        const quantity = form.querySelector(`[name="cantidad_devolucion_${check.value}"]`);
        if (!quantity) return;

        quantity.disabled = !check.checked;
        check.addEventListener('change', () => {
          quantity.disabled = !check.checked;
          if (check.checked && Number(quantity.value) < 1) quantity.value = 1;
        });
      });

      form.addEventListener('submit', (event) => {
        const nextAction = event.submitter?.value !== 'atras';
        if (!nextAction) return;

        if (productChecks.length && !productChecks.some((check) => check.checked)) {
          event.preventDefault();
          window.alert('Selecciona al menos un producto para continuar.');
        }
      });
    }

    // 1b. Devoluciones a proveedores: proveedor → compra → producto → cantidad
    const formProv = document.getElementById('formDevolucionProveedor');
    if (formProv && !formProv.dataset.ready) {
      formProv.dataset.ready = '1';
      const provSelect = document.getElementById('id_devprov_proveedor');
      const compraSelect = document.getElementById('id_devprov_compra');
      const compraHint = document.getElementById('devprovCompraHint');
      const itemsBox = document.getElementById('devprovItems');
      const detalleInput = document.getElementById('id_devprov_detalle');
      const cantInput = document.getElementById('id_devprov_cantidad');
      const stockHint = document.getElementById('devprovStockHint');
      const totalEl = document.getElementById('devprovTotal');
      const fmt = new Intl.NumberFormat('es-CO');
      const urlBase = '/devoluciones/proveedor/';
      let compras = [];
      let itemSel = null;

      function esc(t) {
        const d = document.createElement('div');
        d.textContent = t == null ? '' : t;
        return d.innerHTML;
      }

      function actualizarTotal() {
        const c = parseInt(cantInput.value, 10) || 0;
        const p = itemSel ? itemSel.precio : 0;
        totalEl.textContent = '$' + fmt.format(Math.round(c * p));
      }

      function limpiarItem(msg) {
        itemSel = null;
        detalleInput.value = '';
        cantInput.disabled = true;
        cantInput.removeAttribute('max');
        stockHint.textContent = 'Selecciona un producto de la compra.';
        stockHint.classList.remove('is-warn');
        itemsBox.innerHTML = '<div class="dev-items__empty">' + esc(msg) + '</div>';
        actualizarTotal();
      }

      function pintarItems(compra) {
        itemSel = null;
        detalleInput.value = '';
        cantInput.disabled = true;
        actualizarTotal();
        if (!compra.items.length) { limpiarItem('Esta compra no tiene productos.'); return; }
        let html = '<table class="table dev-table align-middle mb-0"><thead><tr>' +
          '<th></th><th>Producto</th><th class="text-center">Comprada</th>' +
          '<th class="text-center">Ya devuelta</th><th class="text-center">Disponible</th>' +
          '<th class="text-end">Precio</th></tr></thead><tbody>';
        compra.items.forEach(function(it) {
          const ok = compra.devolvible && it.disponible > 0;
          html += '<tr class="' + (ok ? 'dev-item-row' : 'is-unavailable') + '" data-id="' + it.detalle_id + '">' +
            '<td><input type="radio" name="_item" class="form-check-input" ' + (ok ? '' : 'disabled') + '></td>' +
            '<td><strong>' + esc(it.producto) + '</strong>' + (it.lote ? '<small class="d-block text-muted">Lote ' + esc(it.lote) + '</small>' : '') + '</td>' +
            '<td class="text-center">' + it.comprada + '</td>' +
            '<td class="text-center">' + it.devuelta + '</td>' +
            '<td class="text-center"><strong>' + it.disponible + '</strong></td>' +
            '<td class="text-end dev-money">$' + fmt.format(Math.round(it.precio)) + '</td></tr>';
        });
        html += '</tbody></table>';
        itemsBox.innerHTML = html;

        itemsBox.querySelectorAll('.dev-item-row').forEach(function(row) {
          row.addEventListener('click', function() {
            const it = compra.items.find(function(x) { return String(x.detalle_id) === row.dataset.id; });
            if (!it) return;
            itemSel = it;
            detalleInput.value = it.detalle_id;
            itemsBox.querySelectorAll('tr').forEach(function(r) { r.classList.remove('is-selected'); });
            row.classList.add('is-selected');
            row.querySelector('input').checked = true;
            itemsBox.classList.remove('is-invalid');
            cantInput.disabled = false;
            cantInput.max = it.disponible;
            cantInput.value = Math.min(parseInt(cantInput.value, 10) || 1, it.disponible) || 1;
            stockHint.textContent = 'Puedes devolver hasta ' + it.disponible + ' unidades (de ' + it.comprada + ' compradas).';
            stockHint.classList.remove('is-warn');
            actualizarTotal();
          });
        });
      }

      async function cargarCompras() {
        compras = [];
        compraSelect.innerHTML = '<option value="">Cargando compras...</option>';
        compraSelect.disabled = true;
        compraHint.textContent = '';
        limpiarItem('Elige una compra para ver sus productos.');
        if (!provSelect.value) {
          compraSelect.innerHTML = '<option value="">Primero elige un proveedor</option>';
          return;
        }
        try {
          const r = await fetch(urlBase + encodeURIComponent(provSelect.value) + '/compras/', { credentials: 'same-origin' });
          compras = (await r.json()).compras || [];
        } catch (err) {
          compraSelect.innerHTML = '<option value="">No se pudieron cargar las compras</option>';
          return;
        }
        if (!compras.length) {
          compraSelect.innerHTML = '<option value="">Este proveedor no tiene compras</option>';
          compraHint.textContent = 'No hay compras registradas a este proveedor.';
          compraHint.classList.add('is-warn');
          return;
        }
        compraHint.classList.remove('is-warn');
        compraSelect.innerHTML = '<option value="">-- Selecciona una compra --</option>' + compras.map(function(c) {
          return '<option value="' + c.id + '">Compra #' + c.id + ' · ' + c.fecha + ' · $' + fmt.format(Math.round(c.valor)) +
            ' · ' + esc(c.estado_label) + (c.devolvible ? '' : ' (no recibida)') + '</option>';
        }).join('');
        compraSelect.disabled = false;
      }

      provSelect.addEventListener('change', cargarCompras);
      compraSelect.addEventListener('change', function() {
        const c = compras.find(function(x) { return String(x.id) === compraSelect.value; });
        compraHint.classList.remove('is-warn');
        compraHint.textContent = '';
        if (!c) { limpiarItem('Elige una compra para ver sus productos.'); return; }
        if (!c.devolvible) {
          compraHint.textContent = 'Esta compra aún no fue recibida; solo se devuelve mercancía recibida.';
          compraHint.classList.add('is-warn');
        }
        pintarItems(c);
      });
      cantInput.addEventListener('input', actualizarTotal);

      actualizarTotal();
    }

    // 2. Acordeón de Historial de Clientes
    const historyToggle = document.getElementById('devHistoryToggle');
    const historyBody = document.getElementById('devHistoryBody');

    if (historyToggle && historyBody) {
      // Remover listener previo clonando o limpiando
      historyToggle.onclick = function() {
        const isOpen = !historyBody.classList.contains('d-none');
        historyBody.classList.toggle('d-none', isOpen);
        historyToggle.setAttribute('aria-expanded', String(!isOpen));
        if (!isOpen) {
          initTablaDevolucionesClientes();
        }
      };
    }

    // Botones de impresión (para comprobantes y detalles)
    document.querySelectorAll('.btn-print, .btn-print-action, #btnImprimirComprobante').forEach(function(btn) {
      btn.onclick = function(e) {
        e.preventDefault();
        window.print();
      };
    });

    // Inicializar ambas tablas
    initTablaDevolucionesClientes();
    initTablaDevolucionesProveedor();
  }

  // 3. Tabla Devoluciones Clientes (#tablaDevoluciones)
  function initTablaDevolucionesClientes() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const $table = jQuery('#tablaDevoluciones');
    if (!$table.length) return;

    if (jQuery.fn.DataTable.isDataTable($table)) {
      $table.DataTable().destroy();
    }

    const dt = $table.DataTable({
      responsive: true,
      paging: false,
      searching: false,
      lengthChange: false,
      info: false,
      order: [[5, 'desc']],
      columnDefs: [{ targets: [6], orderable: false, searchable: false }],
      language: {
        emptyTable: 'No hay devoluciones registradas.',
        zeroRecords: 'No encontramos coincidencias.'
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: null,
        bottomEnd: null
      },
      buttons: [
        {
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
          className: 'cys-dt-btn-excel',
          title: 'Devoluciones_Clientes_CYS',
          filename: 'Devoluciones_Clientes_CYS',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] }
        },
        {
          extend: 'pdfHtml5',
          text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
          className: 'cys-dt-btn-pdf',
          title: 'Distribuciones CYS Ltda - Historial de Devoluciones (Clientes)',
          filename: 'Devoluciones_Clientes_CYS',
          orientation: 'landscape',
          pageSize: 'A4',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5] },
          customize: function (doc) {
            doc.defaultStyle.fontSize = 9;
            if (doc.styles && doc.styles.tableHeader) {
              doc.styles.tableHeader.fontSize = 10;
              doc.styles.tableHeader.bold = true;
              doc.styles.tableHeader.fillColor = '#011936';
              doc.styles.tableHeader.color = '#CF9C48';
              doc.styles.tableHeader.alignment = 'center';
            }
          }
        }
      ]
    });

    const exportContainer = document.getElementById('cys-dt-export-devoluciones');
    if (exportContainer) {
      if (window.cysCrearDropdownExportar) {
        window.cysCrearDropdownExportar(dt, exportContainer);
      } else {
        exportContainer.innerHTML = '';
        dt.buttons().container().removeClass('d-none').appendTo(exportContainer);
      }
    }
  }

  // 4. Tabla Devoluciones Proveedor (#tablaDevolucionesProveedor)
  function initTablaDevolucionesProveedor() {
    if (!window.jQuery || !jQuery.fn.DataTable) return;
    const $tableProv = jQuery('#tablaDevolucionesProveedor');
    if (!$tableProv.length) return;

    if (jQuery.fn.DataTable.isDataTable($tableProv)) {
      $tableProv.DataTable().destroy();
    }

    const dtProv = $tableProv.DataTable({
      responsive: true,
      paging: false,
      searching: true,
      lengthChange: false,
      info: false,
      order: [[0, 'desc']],
      columnDefs: [{ targets: [8], orderable: false, searchable: false }],
      language: {
        emptyTable: 'No hay devoluciones a proveedores registradas.',
        zeroRecords: 'No se encontraron registros.'
      },
      layout: {
        topStart: null,
        topEnd: null,
        bottomStart: null,
        bottomEnd: null
      },
      buttons: [
        {
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill me-1"></i> Excel',
          className: 'cys-dt-btn-excel',
          title: 'Devoluciones_Proveedores_CYS',
          filename: 'Devoluciones_Proveedores_CYS',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5, 6, 7] }
        },
        {
          extend: 'pdfHtml5',
          text: '<i class="bi bi-file-earmark-pdf-fill me-1"></i> PDF',
          className: 'cys-dt-btn-pdf',
          title: 'Distribuciones CYS Ltda - Devoluciones a Proveedores',
          filename: 'Devoluciones_Proveedores_CYS',
          orientation: 'landscape',
          pageSize: 'A4',
          exportOptions: { columns: [0, 1, 2, 3, 4, 5, 6, 7] },
          customize: function (doc) {
            doc.defaultStyle.fontSize = 9;
            if (doc.styles && doc.styles.tableHeader) {
              doc.styles.tableHeader.fontSize = 10;
              doc.styles.tableHeader.bold = true;
              doc.styles.tableHeader.fillColor = '#011936';
              doc.styles.tableHeader.color = '#CF9C48';
              doc.styles.tableHeader.alignment = 'center';
            }
          }
        }
      ]
    });

    const txt = document.getElementById('filtroProvTexto');
    const est = document.getElementById('filtroProvEstado');
    if (txt) txt.oninput = function() { dtProv.search(this.value).draw(); };
    if (est) est.onchange = function() { dtProv.column(7).search(this.value).draw(); };

    const contProv = document.getElementById('cys-dt-export-dev-proveedor');
    if (contProv) {
      if (window.cysCrearDropdownExportar) {
        window.cysCrearDropdownExportar(dtProv, contProv);
      } else {
        contProv.innerHTML = '';
        dtProv.buttons().container().removeClass('d-none').appendTo(contProv);
      }
    }
  }

  // Exponer globalmente
  window.initDevolucionesTables = initDevolucionesPage;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDevolucionesPage);
  } else {
    initDevolucionesPage();
  }

  if (document.body) {
    document.body.addEventListener('htmx:afterSettle', initDevolucionesPage);
  }
})();
