<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body>
    %for letter in objects :
    <% setLang(letter.partner_lang) %>
    <table class="dest_address">
        <tr><td><b>${letter.partner_id.title or ''|entity}  ${letter.partner_id.name |entity}</b></td></tr>
		<tr><td>${letter.partner_contact or ''|entity}</td></tr>
        <tr><td>${letter.partner_address_id.street or ''|entity}</td></tr>
        <tr><td>${letter.partner_address_id.street2 or ''|entity}</td></tr>
        <tr><td>${letter.partner_address_id.zip or ''|entity} ${letter.partner_address_id.city or ''|entity}</td></tr>
        %if letter.partner_address_id.country_id :
        <tr><td>${letter.partner_address_id.country_id.name or ''|entity} </td></tr>
        %endif
        %if letter.partner_address_id.phone :
        <tr><td>${_("Tel")}: ${letter.partner_address_id.phone|entity}</td></tr>
        %endif
        %if letter.partner_address_id.fax :
        <tr><td>${_("Fax")}: ${letter.partner_address_id.fax|entity}</td></tr>
        %endif
        %if letter.partner_address_id.email :
        <tr><td>${_("E-mail")}: ${letter.partner_address_id.email|entity}</td></tr>
        %endif
    </table>
    <br/>
	<br/>
	<br/>
	<table class="subject">
		<tr><td><b><u>${_("Subject")}</u></b>:&nbsp;${letter.subject or ''|entity}</td></tr>	
		<tr><td><b><u>${_("Reference")}</u></b>:&nbsp;${letter.name or ''|entity}</td></tr>
	</table>
    <br/>
    <br/>
	<p>
		${letter.intro.replace('\n','<br/>')}
    </p>
	<br/>
	<br/>
	<table class="table_noborder_left_12">
		<tr><td>${_("Start Date")}:</td><td>${formatLang(letter.date_start, date=True)|entity}</td></tr>
		<tr><td>${_("Maturity Date")}:</td><td>${formatLang(letter.date_stop, date=True)|entity}</td></tr>
		<tr><td>${_("Transaction Amount")}:</td><td>${formatLang(letter.amount_main)}&nbsp;${letter.journal_id.currency.symbol or ''|entity}</td></tr>
		<tr><td>${_("Interest Rate")}:</td><td>${formatLang(letter.rate)}&nbsp;${_("% per year")|entity}</td></tr>
		<tr><td>${_("Interest Payment")}:</td><td>${get_selection_label(letter,'interest_payment',letter.interest_payment) or ''|entity}</td></tr>
		<tr><td>${_("Interest Amount")}:</td><td>${formatLang(letter.amount_interest)}&nbsp;${letter.journal_id.currency.symbol or ''|entity}</td></tr>
		<tr><td>${_("Transaction Costs")}:</td><td>${formatLang(letter.amount_cost)}&nbsp;${letter.journal_id.currency.symbol or ''|entity}</td></tr>
		<tr><td>${_("Bank Account")}:</td><td>${format_bank(letter.bank_id)|entity}</td></tr>	
	</table>		
	<br/>
	<br/>
	<p>
		${letter.close.replace('\n','<br/>') or ''}
    </p>
	%endfor
</body>
</html>