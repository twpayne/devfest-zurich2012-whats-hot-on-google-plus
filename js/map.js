var mapDiv = document.getElementById('map');
var map = new google.maps.Map(mapDiv, {
  mapTypeId: google.maps.MapTypeId.SATELLITE
});
map.fitBounds(new google.maps.LatLngBounds(new google.maps.LatLng(-90, -180), new google.maps.LatLng(90, 180)));

var layer = new google.maps.FusionTablesLayer({
  heatmap: {
    enabled: true
  }
});
var query = {
  select: 'geocode',
  from: '1O7qsDkkgaDbAArUKywHVwPxVqz4RA9P1xEAfrHU',
  where: 'query LIKE "sunrise"'
};
layer.setOptions({query: query});
layer.setMap(map);
