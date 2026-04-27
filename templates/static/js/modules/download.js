const getCellValue = (cell) => {
  const field = cell.querySelector('input, select, textarea');
  if (field) {
    return `${field.value || ''}`.trim();
  }
  return `${cell.textContent || ''}`.trim();
};

const collectTableData = (table, index) => {
  const section = table.closest('.subscreen, .screen');
  const sectionId = section ? section.id : `tabla_${index + 1}`;
  const sheetName = sectionId.replace(/^sub-/, '').replace(/^screen-/, '').slice(0, 31) || `tabla_${index + 1}`;

  const headerCells = Array.from(table.querySelectorAll('thead th')).map((th) => th.textContent.trim());
  const bodyRows = Array.from(table.querySelectorAll('tbody tr')).map((row) =>
    Array.from(row.querySelectorAll('td')).map((td) => getCellValue(td))
  );

  const nonEmptyRows = bodyRows.filter((row) => row.some((value) => value !== ''));

  if (!headerCells.length || !nonEmptyRows.length) {
    return null;
  }

  return { sheetName, headers: headerCells, rows: nonEmptyRows };
};

const applyWorksheetStyles = (worksheet, columnCount, rowCount) => {
  for (let c = 1; c <= columnCount; c += 1) {
    const headerCell = worksheet.getCell(1, c);
    headerCell.font = { bold: true, color: { argb: 'FFFFFFFF' }, name: 'Calibri', size: 11 };
    headerCell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF002E5D' },
    };
    headerCell.alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
    headerCell.border = {
      top: { style: 'thin', color: { argb: 'FFB8C7DB' } },
      left: { style: 'thin', color: { argb: 'FFB8C7DB' } },
      bottom: { style: 'thin', color: { argb: 'FFB8C7DB' } },
      right: { style: 'thin', color: { argb: 'FFB8C7DB' } },
    };
  }

  for (let r = 2; r <= rowCount + 1; r += 1) {
    for (let c = 1; c <= columnCount; c += 1) {
      const cell = worksheet.getCell(r, c);
      cell.font = { name: 'Calibri', size: 10, color: { argb: 'FF1F3550' } };
      cell.alignment = { horizontal: 'left', vertical: 'middle', wrapText: true };
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: r % 2 === 0 ? 'FFF8FBFF' : 'FFFFFFFF' },
      };
      cell.border = {
        top: { style: 'thin', color: { argb: 'FFD7E2F1' } },
        left: { style: 'thin', color: { argb: 'FFD7E2F1' } },
        bottom: { style: 'thin', color: { argb: 'FFD7E2F1' } },
        right: { style: 'thin', color: { argb: 'FFD7E2F1' } },
      };
    }
  }

  worksheet.views = [{ state: 'frozen', ySplit: 1 }];
};

const setColumnWidths = (worksheet, headers, rows) => {
  worksheet.columns = headers.map((header, index) => {
    const maxDataLength = rows.reduce((max, row) => Math.max(max, `${row[index] || ''}`.length), 0);
    const width = Math.min(50, Math.max(14, header.length + 2, maxDataLength + 2));
    return { width };
  });
};

export const downloadData = async () => {
  if (!window.ExcelJS) {
    alert('No fue posible cargar el exportador de Excel. Recarga la página e intenta nuevamente.');
    return;
  }

  const tables = Array.from(document.querySelectorAll('table.emisiones-table'));
  const tableData = tables
    .map((table, index) => collectTableData(table, index))
    .filter(Boolean);

  if (!tableData.length) {
    alert('No hay datos diligenciados en las tablas para exportar.');
    return;
  }

  try {
    const workbook = new window.ExcelJS.Workbook();
    workbook.creator = 'Universidad ECCI';
    workbook.created = new Date();

    tableData.forEach(({ sheetName, headers, rows }) => {
      const worksheet = workbook.addWorksheet(sheetName);
      worksheet.addRow(headers);
      rows.forEach((row) => worksheet.addRow(row));
      setColumnWidths(worksheet, headers, rows);
      applyWorksheetStyles(worksheet, headers.length, rows.length);
    });

    const buffer = await workbook.xlsx.writeBuffer();
    const blob = new Blob([
      buffer,
    ], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `inventario-ecci-${new Date().toISOString().slice(0, 10)}.xlsx`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error(error);
    alert('No fue posible generar el archivo Excel. Intenta nuevamente.');
  }
};

export const initDownloadButton = () => {
  const downloadButton = document.getElementById('downloadBtn');
  if (!downloadButton) {
    return;
  }
  downloadButton.addEventListener('click', downloadData);
};
