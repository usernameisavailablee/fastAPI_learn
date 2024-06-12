document.addEventListener('DOMContentLoaded', (event) => {
    var map = L.map('map').setView([45.0355, 38.9753], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    var coordinates = [];
    var routeLayer;

    map.on('click', function(e) {
        var latLng = e.latlng;
        var coordinate = {
            latitude: latLng.lat,
            longitude: latLng.lng
        };
        coordinates.push(coordinate);
        L.marker(latLng).addTo(map);
        updateCoordinatesDisplay();
    });

    var geocoder = L.Control.Geocoder.nominatim();

    document.getElementById('address-input').addEventListener('input', function() {
        var query = this.value;
        if (query.length > 2) {
            geocoder.geocode(query, function(results) {
                var list = document.getElementById('address-list');
                list.innerHTML = '';
                results.forEach(function(result) {
                    var li = document.createElement('li');
                    li.textContent = result.name;
                    li.dataset.lat = result.center.lat;
                    li.dataset.lng = result.center.lng;
                    li.addEventListener('click', function() {
                        var lat = parseFloat(this.dataset.lat);
                        var lng = parseFloat(this.dataset.lng);
                        var latLng = {
                            latitude: lat,
                            longitude: lng
                        };
                        coordinates.push(latLng);
                        L.marker([lat, lng]).addTo(map);
                        map.setView([lat, lng], 13);
                        updateCoordinatesDisplay();
                        list.innerHTML = '';
                    });
                    list.appendChild(li);
                });
            });
        }
    });

    function updateCoordinatesDisplay() {
        var list = document.getElementById('selected-points');
        list.innerHTML = '';
        coordinates.forEach((coord, index) => {
            var li = document.createElement('li');
            li.textContent = `Point ${index + 1}: (${coord.latitude.toFixed(5)}, ${coord.longitude.toFixed(5)})`;
            var removeButton = document.createElement('button');
            removeButton.classList.add('remove'); // добавляем класс 'remove'
            removeButton.textContent = 'Удалить';
            removeButton.addEventListener('click', function() {
                coordinates.splice(index, 1);
                updateCoordinatesDisplay();
                map.eachLayer(function(layer) {
                    if (layer instanceof L.Marker && layer.getLatLng().equals([coord.latitude, coord.longitude])) {
                        map.removeLayer(layer);
                    }
                });
            });
            li.appendChild(removeButton);
            list.appendChild(li);
        });
        document.getElementById('coordinates').value = JSON.stringify(coordinates);
    }

    document.getElementById('optimize').addEventListener('click', function() {
        var formData = new FormData();
        formData.append('coordinates', JSON.stringify(coordinates));

        fetch('/submit/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (routeLayer) {
                map.removeLayer(routeLayer);
            }

            var routeCoordinates = data.route.map(coord => L.latLng(coord[0], coord[1]));

            routeLayer = L.Routing.control({
                waypoints: routeCoordinates,
                routeWhileDragging: false,
                lineOptions: {
                    styles: [{color: 'blue', opacity: 0.8, weight: 5}]
                },
                createMarker: function() { return null; }
            }).addTo(map);
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
