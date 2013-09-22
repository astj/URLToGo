	$('#bm-tab a').click(function (e) {
		e.preventDefault();
		$(this).tab('show');
});

$('.pop_over').popover();

$('.tool_tip').tooltip();