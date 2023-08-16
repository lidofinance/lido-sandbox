from IPython.display import HTML, display

def print_table(data: list[list], head: list[str]):
    html = "<table>"

    if head:
        html += "<tr>"
        for h in head:
            html += "<th>%s</th>"%(h)
        html += "</tr>"

    for row in data:
        html += "<tr>"
        for col in row:
            if isinstance(col, float):
                html += "<td align='right'>%s</td>"%(round(col, 4))
            elif isinstance(col, int):
                html += "<td align='right'>%d</td>"%(col)
            else:
                html += "<td align='left'>%s</td>"%(col)
        html += "</tr>"

    html += "</table>"

    display(HTML(html))