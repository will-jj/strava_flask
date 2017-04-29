(function () {

  'use strict';

  angular.module('WordcountApp', [])

  .controller('WordcountController', ['$scope', '$log', '$http', '$timeout',
    function($scope, $log, $http, $timeout) {

    $scope.submitButtonText = 'Submit';
    $scope.loading = false;
    $scope.urlerror = false;

    $scope.getResults = function() {

      $log.log('test');

      // get the URL from the input
        var userInput = $scope.url;
      $scope.data = null
      $scope.url = "dont break"
      // fire the API request
      $http.post('/start', {'url': userInput}).
        success(function(results) {
          $log.log(results);
          getWordCount(results);
          $scope.data = null;
          $scope.loading = true;
          $scope.submitButtonText = 'Loading...';
          $scope.urlerror = false;
        }).
        error(function(error) {
          $log.log(error);
        });

    };

    myApp.directive('stravaChart', function(){
  function link(scope, el, attr){
    var color = d3.scale.category10();
    var width = 200;
    var height = 200;
    var min = Math.min(width, height);
    var svg = d3.select(el[0]).append('svg');
    var pie = d3.layout.pie().sort(null);
    var arc = d3.svg.arc()
      .outerRadius(min / 2 * 0.9)
      .innerRadius(min / 2 * 0.5);

    svg.attr({width: width, height: height});

    // center the donut chart
    var g = svg.append('g')
      .attr('transform', 'translate(' + width / 2 + ',' + height / 2 + ')');

    // add the <path>s for each arc slice
    var arcs = g.selectAll('path');

    scope.$watch('data', function(data){
      if(!data){ return; }
      arcs = arcs.data(pie(data));
      arcs.exit().remove();
      arcs.enter().append('path')
        .style('stroke', 'white')
        .attr('fill', function(d, i){ return color(i) });
      // update all the arcs (not just the ones that might have been added)
      arcs.attr('d', arc);
    }, true);
  }
  return {
    link: link,
    restrict: 'E',
    scope: { data: '=' }
  };
});


    function getWordCount(jobID) {

      var timeout = '';

      var poller = function() {
        // fire another request
        $http.get('/results?jobid='+jobID).
          success(function(data, status, headers, config) {
            if(status === 202) {
              $log.log(data, status);
            } else if (status === 200){
              //$log.log(data);
              $scope.loading = false;
              $scope.submitButtonText = "Submit";
             // $scope.b= JSON.parse(data);


              $scope.data = data;
              $log.log($scope.data)
              $timeout.cancel(timeout);
              //do_plot(data);
              return false;
            }
            // continue to call the poller() function every 2 seconds
            // until the timeout is cancelled
            timeout = $timeout(poller, 2000);
          }).
          error(function(error) {
            $log.log(error);
            $scope.loading = false;
            $scope.submitButtonText = "Submit";
            $scope.urlerror = true;
          });
      };

      poller();

    }

  }])



}());
