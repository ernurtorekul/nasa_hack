import { useState } from "react";
import "./App.css";

function App() {
  const [city, setCity] = useState("");
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchWeather = async () => {
    if (!city.trim()) {
      setError("Please enter a city name");
      return;
    }

    setLoading(true);
    setError("");
    setWeather(null);

    try {
      const response = await fetch(
        `http://localhost:8000/weather?city=${encodeURIComponent(city.trim())}`
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to fetch weather data");
      }

      const data = await response.json();
      setWeather(data);
    } catch (err) {
      setError(err.message || "An error occurred while fetching weather data");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchWeather();
  };

  const getWeatherIcon = (iconCode) => {
    return `https://openweathermap.org/img/wn/${iconCode}@2x.png`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const options = { weekday: "short", month: "short", day: "numeric" };
    return date.toLocaleDateString("en-US", options);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-md mx-auto">
          <h1 className="text-4xl font-bold text-center text-blue-800 mb-8">
            WeatherSphere
          </h1>

          <form onSubmit={handleSubmit} className="mb-8">
            <div className="flex gap-2">
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Enter city name..."
                className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? "Loading..." : "Search"}
              </button>
            </div>
          </form>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600 text-center">{error}</p>
            </div>
          )}

          {loading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading weather data...</p>
            </div>
          )}

          {weather && !loading && (
            <div className="bg-white rounded-2xl shadow-xl p-6">
              <div className="text-center mb-4">
                <h2 className="text-2xl font-semibold text-gray-800">
                  {weather.current.city}, {weather.current.country}
                </h2>
                <p className="text-gray-500 capitalize">
                  {weather.current.description}
                </p>
              </div>

              <div className="flex items-center justify-center mb-6">
                <img
                  src={getWeatherIcon(weather.current.icon)}
                  alt={weather.current.description}
                  className="w-24 h-24 mr-4"
                />
                <div className="text-5xl font-bold text-gray-800">
                  {Math.round(weather.current.temperature)}°C
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm mb-6">
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-gray-600">Feels like</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {Math.round(weather.current.feels_like)}°C
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-gray-600">Humidity</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {weather.current.humidity}%
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-gray-600">Wind Speed</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {weather.current.wind_speed} m/s
                  </p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-gray-600">Pressure</p>
                  <p className="text-lg font-semibold text-gray-800">
                    {weather.current.pressure} hPa
                  </p>
                </div>
              </div>

              {/* Forecast Section */}
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">
                  5-Day Forecast
                </h3>
                <div className="overflow-x-auto">
                  <div className="flex gap-3 pb-2">
                    {weather.forecast.slice(0, 5).map((day, index) => (
                      <div
                        key={index}
                        className="flex-shrink-0 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 text-center min-w-[100px] border border-blue-100"
                      >
                        <p className="text-sm font-medium text-gray-700 mb-2">
                          {formatDate(day.date)}
                        </p>
                        <img
                          src={getWeatherIcon(day.icon)}
                          alt={day.description}
                          className="w-12 h-12 mx-auto mb-2"
                        />
                        <p className="text-sm text-gray-600 capitalize mb-2">
                          {day.description}
                        </p>
                        <div className="flex justify-center gap-2 text-sm">
                          <span className="font-semibold text-gray-800">
                            {Math.round(day.temp_max)}°
                          </span>
                          <span className="text-gray-500">
                            {Math.round(day.temp_min)}°
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
