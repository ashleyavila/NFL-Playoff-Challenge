var picks = JSON.parse($('#picksHolder').prop("value"));

$(".input-group").click(function(){
	var pick = $(this).parent().attr("id");
	var opponent = pick.substring(0,8) + (pick[8]==='1' ?  '2' : '1')
	
	if($('#'+opponent).hasClass("selected")){
		$('#'+opponent).removeClass("selected");
		$('#'+opponent).find('.input-group-addon').addClass('points-hidden');
		$('#'+opponent).find('button').prop('disabled', true);
		$('#'+opponent).find('.dropdown-toggle').html('0 <span class="caret"></span>')
		picks[opponent] = 0;
	}
	
	// console.log(pick + " selected vs "+ opponent );
	$(this).parent().addClass("selected");
	$(this).find('button').prop('disabled', false);
})

$(".dropdown-menu li a").click(function(){

  var selText = $(this).text();
  console.log(selText)
  $(this).parents('.input-group-btn').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
  picks[$(this).parents('td').prop('id')] = parseInt(selText);

  $('#picksHolder').prop("value", JSON.stringify(picks));
});

function setup() {
	
	console.log(picks)
	for(var pick in picks) {
		$('#'+pick).addClass("selected");
		$('#'+pick).find('.dropdown-toggle').html(picks[pick] + ' <span class="caret"></span>')
		$('#'+pick).find('button').prop('disabled', false);

	}
}

setup()