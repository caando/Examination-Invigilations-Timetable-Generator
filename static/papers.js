$(function () {
	$('.datetimepicker1').datetimepicker({
		format: 'DD-MM-YYYY',
		daysOfWeekDisabled: [0, 6],
		useCurrent: false,
		Default: false
	});
	$('.datetimepicker2').datetimepicker({
		format: 'LT'
	});
	$('.datetimepicker3').datetimepicker({
		format: 'LT'
	});
	$(".datetimepicker2").on("change.datetimepicker", function (e) {
		$('.datetimepicker3').datetimepicker('minDate', e.date);
	});
	$(".datetimepicker3").on("change.datetimepicker", function (e) {
		$('.datetimepicker2').datetimepicker('maxDate', e.date);
	});
});
