var app = angular.module('video', []);

app.controller('video_query', ($scope, $http)=>{
    $scope.playState = 0;
    $scope.query = ()=>{
        console.log($scope.cols);
        console.log($scope.command);
        $http({
            method: 'GET',
            url: '/query?command='+$scope.command.trim()+"&cols="+$scope.cols.trim(),
            data: $scope.command
        }).then((res)=>{
            $scope.results = res.data;
            if($scope.results.length>0){
                $scope.src = 'data:image/jpeg;base64,'+$scope.results[0].frame;
                $scope.index = 0;
            }
        }, (err)=>{
            console.log(err);
        });
    }

    $scope.next = ()=>{
        $scope.index += 1;
        if($scope.index>=$scope.results.length)
            $scope.index = 0;
        $scope.src = 'data:image/jpeg;base64,'+$scope.results[$scope.index].frame;
     
    }

    $scope.prev = ()=>{
        $scope.index -= 1;
        if($scope.index < 0)
            $scope.index = $scope.results.length-1;
        $scope.src = 'data:image/jpeg;base64,'+$scope.results[$scope.index].frame;
    }

    $scope.play = ()=>{
        if($scope.playState == 0){
            setInterval(()=>{
                $scope.next();
                
            }, 300)
        }
    }
});