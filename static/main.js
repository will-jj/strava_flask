
var strava_ang = angular.module('strava_ang', ['nvd3ChartDirectives']);

strava_ang.config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{a');
  $interpolateProvider.endSymbol('a}');
}]);
  strava_ang.controller('strava_ang', function($scope, $http){

    // calling the api, grabbing the value for USD, appending it to the dom
    $scope.init = function(a){
      $scope.a = JSON.stringify(a);
      $scope.b = JSON.parse($scope.a);

};


    $scope.xAxisTickFormatFunctionOLD = function(){
      return function(date){
        return d3.time.format('%x')(new Date(date));
      };
    };

    $scope.xAxisTickFormatFunction = function(){
      return function(date){
        return (date);
      };
    };






  });

