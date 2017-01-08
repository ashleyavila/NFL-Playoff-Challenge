var picks = JSON.parse($('#picksHolder').prop("value"));
var correctpicks = JSON.parse($('#correctpicksHolder').prop("value"));
var tiebreakers = JSON.parse($('#tiebreakerHolder').prop("value"));

$(".input-group").click(function(){
	if (!$(this).parent().hasClass("selectable")) {
		return
	}
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

$(".sbscoreinput").keyup(function(){
	var score = parseInt($(this).val())
	tiebreakers[$(this).prop('id').slice(-1)] = score
	console.log(tiebreakers)
	$('#tiebreakerHolder').prop("value", JSON.stringify(tiebreakers));
})

function setup() {
	
	console.log(correctpicks)
	console.log(tiebreakers)
	for(var pick in picks) {
		$('#'+pick).addClass("selected");
		if ($('#'+pick).hasClass("selectable")){
			$('#'+pick).find('.dropdown-toggle').html(picks[pick] + ' <span class="caret"></span>')
			$('#'+pick).find('button').prop('disabled', false);
			$('#'+pick).find('.time-slot').css('color','grey')
		} else {
			$('#'+pick).find('.dropdown-toggle').html(picks[pick] + ' <span class="caret nocaret"></span>')

		}
		var week = pick[4];
		var game = pick[6];
		var team = pick[8];
		if(correctpicks[week][game] == team){
			$('#'+pick).addClass("correct");
		}
		else if(correctpicks[week][game] != 0 && correctpicks[week][game] != team){
			$('#'+pick).addClass("incorrect");
		}

	}
	$('#sbscore1').val(tiebreakers["1"])
	$('#sbscore2').val(tiebreakers["2"])
}

setup()