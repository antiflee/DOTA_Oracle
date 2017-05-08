setTimeout(function () {
    $('#goBack').show().addClass('animated fadeIn');}, 850
);

(function() {
  var radianceHeroes = document.getElementsByClassName("radianceHeroes");
  var direHeroes = document.getElementsByClassName("direHeroes");
  TweenMax.staggerFrom(direHeroes, 1, {x:"+=350"}, 0.1);
  TweenMax.staggerFrom(radianceHeroes, 1, {x:"-=350"}, 0.1);
}
)();
