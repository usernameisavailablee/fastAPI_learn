document.addEventListener('DOMContentLoaded', (event) => {
    var map = L.map('map').setView([45.0355, 38.9753], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var coordinates = [];

    map.on('click', function(e) {
        var latLng = e.latlng;
        var coordinate = {
            latitude: latLng.lat,
            longitude: latLng.lng
        };
        coordinates.push(coordinate);
        L.marker(latLng).addTo(map);
        document.getElementById('coordinates').value = JSON.stringify(coordinates);
    });
});
