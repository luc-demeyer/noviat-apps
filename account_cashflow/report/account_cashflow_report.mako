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
    days_per_page = 7
    nbr_pages = int(ceil(float(nbr_days)/days_per_page))
    page_count = 0
  %>
  %for page in range(nbr_pages):
    <% 
      page_count += 1
      page_date_start_index = (page_count - 1) * days_per_page
      page_date_stop_index = ((page_count == nbr_pages) and (len(days) - 1)) or (page_date_start_index + days_per_page - 1)
      page_date_start = days[page_date_start_index]
      page_date_stop = days[page_date_stop_index]
      page_days = days[page_date_start_index:page_date_stop_index + 1]
      report_title = toplevel_cfc.name + '  -  ' + _('Cash Flow Report') + ': ' + formatLang(date_start, date=True) + '..' + formatLang(date_stop, date=True)
    %>
    %if page_count > 1:
      <p class="report_title" style="page-break-before:always;"><br>${report_title|entity}</p>
    %else:
      <p class="report_title" style="margin-top:15px">${report_title|entity}</p>
    %endif
    <table class="list_table" width="100%">
      <thead>
        <% col_cnt = 0 %>
        <tr>
          <th width="8%">${_("Code")}</th>
          <th width="20%">${_("Description")}</th>
          %for day in page_days:
            %if col_cnt < days_per_page:
              <th width="9%" class="amount">${formatLang(day, date=True)}</th>
              <% col_cnt += 1 %>
            %endif
          %endfor
          %if col_cnt < days_per_page:
            %for x in range(1,days_per_page - col_cnt):
              <th width="9%"/>
            %endfor       
          %endif
          <th width="9%" class="amount">${(nbr_days == days_per_page) and _("Period Balance") or _("Page Balance")}</th>
          %if page_days[-1] == days[-1] and col_cnt < days_per_page:
            <th width="9%" class="amount">${_("Period Balance")}</th>
          %endif
        </tr>
      </thead>
      <tbody>
        %for cfc in objects[1:]:
          <% col_cnt = 0 %>
          <tr class=${cfc.type}>
            <%
            td_code_style = 'padding-left:' + str(10 * (data['cfc_levels'][cfc.id] - 1)) + 'px'
            %>
            <td style=${td_code_style}>${cfc.code|entity}</td>
            <td>${cfc.name |entity}</td>
            %for day in page_days:
              %if col_cnt < days_per_page:
                <td class="amount">${formatLang(balance_period([cfc.id], day=day))}</td>
                <% col_cnt += 1 %>
              %endif
            %endfor
            %if col_cnt < days_per_page:
              %for x in range(1,days_per_page - col_cnt):
                <td />
              %endfor       
            %endif
            <td class="amount">${formatLang(balance_period([cfc.id], date_start=page_date_start, date_stop=page_date_stop))}</td>
            %if page_days[-1] == days[-1] and col_cnt < days_per_page:
              <td class="amount">${formatLang(balance_period([cfc.id], date_start=date_start, date_stop=date_stop))}</td>
            %endif
          </tr>
        %endfor
      </tbody>
    </table>
    %if (page_count == nbr_pages) and (col_cnt == days_per_page) and (days_per_page != nbr_days): 
      <p class="report_title" style="page-break-before:always;"><br>${report_title|entity}</p>
      <table class="list_table" width="100%">
        <thead>
          <tr>
            <th width="10%">${_("Code")}</th>
            <th width="30%">${_("Description")}</th>
            <th width="60%" class="amount">${_("Period Balance")}</th>
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
    %endif
  %endfor
</body>
</html>