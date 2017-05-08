var removeHero = function(hero_id, imageUrl) {
  if($.inArray(hero_id, radianceIds) >= 0) {
    // alert($.inArray(hero_id, radianceIds));
    radianceIds.splice($.inArray(hero_id, radianceIds), 1);
    radianceImgs.splice($.inArray(imageUrl, radianceImgs), 1);
    showHideAskOracle();
  } else {
    // alert($.inArray(hero_id, direIds));
    direIds.splice($.inArray(hero_id, direIds), 1);
    direImgs.splice($.inArray(imageUrl, direImgs), 1);
    showHideAskOracle();
  };
};

var findHeroFromInput = function(thisObj, side) {
  var $input = $(thisObj),
      val = $input.val();
      list = $input.attr('list'),
      match = $('#'+list + ' option').filter(function() {
         return ($(this).val() === val);
      });
  if (match.length > 0) {
      var name = match.val();
      var heroId = match.data("heroid").toString();
      var imageUrl = match.data("imageurl");
      $("#direHeroSelect").val("");
      $("#radianceHeroSelect").val("");
      addHeroFromInput(name,imageUrl,heroId,side);
  } else {
  }
}

$("ul").on("click", "li", function(event){
  $(this).toggleClass("animated fadeOutRight");
  var newLen = $(this).parent().find("li").length/5*100-20;
  $(this).parent().parent().parent().find(".progress-bar").css('width',newLen+'%');
  var info = $(this).attr('id').split("-");
  var hero_id = info[0];
  var imageUrl = info[1];
  removeHero(hero_id, imageUrl);
	$(this).fadeOut(150, function(){
		$(this).remove();
	});
	event.stopPropagation();
});

$("#direHeroSelect").on('input', function(event){
    findHeroFromInput($(this),"dire");
  });

$("#radianceHeroSelect").on('input', function(event){
    findHeroFromInput($(this),"radiance");
  });

$("#helpIcon").click(function(event){
  $("#helpDiv").fadeToggle("slow", "linear");
	event.stopPropagation();
});

$("#imgUploadIcon").click(function(event){
  $("#imageUploadDiv").fadeToggle("linear");
	event.stopPropagation();
});

$("body").click(function(){
  $("#helpDiv").fadeOut("linear");
})

$("#uploadButton").click(function(){
  $(".analyzingPicText").fadeIn("linear");
})

// $("input[type='text']").keypress(function(event){
// 	if(event.which === 13){
// 		var todoText = $(this).val();
// 		content = todoText.replace(/</g, "&lt;").replace(/>/g, "&gt;");
// 		$(this).val("");
//     if ($(this).parent().find("li").length < 5) {
// 		    $(this).next().append("<li>"+content+"</li>");
//         var newLen = $(this).parent().find("li").length/5*100;
//         $(this).parent().parent().find(".progress-bar").css('width',newLen+'%');
//     } else {
//       alert("You can only have five heroes on one team.")
//     };
// 	};
// });


// $(".heroesDiv").on("click", ".heroImg", function(){
//   if($("#radiance").find("li").length < 5) {
//     $("#radiance ul").append("<li>"+{{ hero.name|safe }}+"</li>")
//   } else if ($("#dire").find("li").length < 5) {
//     $("#dire ul").append("<li>"+{{ hero.name|safe }}+"</li>")
//   } else {
//     alert("You can only have five heroes on each team.")
//   };
// });
