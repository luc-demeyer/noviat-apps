<html>
<% setLang(lang) %>
<head>
  <title>${_('Cash Flow Report')}</title>
  <style type="text/css">
    ${css}
  </style>
    <% toplevel_cfc = objects[0] %>
</head>
<body>
  <% 
    report_title = toplevel_cfc.name + '  -  ' + _('Cash Flow Summary Report') + ': ' + formatLang(date_start, date=True) + '..' + formatLang(date_stop, date=True)
  %>
  <p class="report_title" style="margin-top:15px">${report_title|entity}</p>
  <table class="list_table" width="100%">
    <thead>
      <tr>
        <th width="15%">${_("Code")}</th>
        <th width="55%">${_("Description")}</th>
        <th width="30%" class="amount">${_("Period Balance")}</th>
      </tr>
    </thead>
    <tbody>
      %for cfc in objects[1:]:
        <tr class=${cfc.type}>
          <%
            td_code_style = 'padding-left:' + str(10 * (data['cfc_levels'][cfc.id] - 1)) + 'px'
          %>
          <td style=${td_code_style}>${cfc.code|entity}</td>
          <td>${cfc.name|entity}</td>
          <td class="amount">${formatLang(balance_period([cfc.id], date_start=date_start, date_stop=date_stop))}</td>
        </tr>
      %endfor
    </tbody>
  </table>
</body>
</html>