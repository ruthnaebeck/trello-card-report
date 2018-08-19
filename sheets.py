def numberToLetters(q):
  q = q - 1
  result = ''
  while q >= 0:
      remain = q % 26
      result = chr(remain+65) + result
      q = q//26 - 1
  return result

def colrow_to_A1(col, row):
    return numberToLetters(col)+str(row)

def update_sheet(ws, rows, left=1, top=2):
  # number of rows and columns
  num_lines, num_columns = len(rows), len(rows[0])

  # selection of the range that will be updated
  cell_list = ws.range(
      colrow_to_A1(left,top)+':'+colrow_to_A1(left+num_columns-1, top+num_lines-1)
  )

  # modifying the values in the range
  for cell in cell_list:
    val = rows[cell.row-top][cell.col-left]
    cell.value = val

  # update in batch
  ws.update_cells(cell_list)
