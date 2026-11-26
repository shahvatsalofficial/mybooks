from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(description="Name of the target city")

class ProductionWeatherTool:
    name: str = "fetch_weather"
    description: str = "Fetch current temperature and conditions for a given city."
    args_schema = WeatherInput

    def _run(self, city: str) -> str:
        # Synchronous execution
        return json.dumps({"city": city, "temp_c": 18, "condition": "Cloudy"})

    async def _arun(self, city: str) -> str:
        # Non-blocking asynchronous execution
        await asyncio.sleep(0.01)
        return self._run(city)
