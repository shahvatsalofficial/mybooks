from pydantic import ValidationError

class ResilientSchemaRunner:
    def __init__(self, client: Anthropic):
        self.client = client
        self.max_retries = 2

    def execute_with_repair(self, input_prompt: str, target_schema: type[BaseModel]) -> BaseModel:
        sanitizer = DeterministicJSONSanitizer()
        current_prompt = input_prompt
        schema_json = json.dumps(target_schema.model_json_schema(), indent=2)

        for attempt in range(self.max_retries + 1):
            res = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.0,
                system=f"Output strictly valid JSON matching this schema:\n{schema_json}\nZero markdown fences or conversational text.",
                messages=[{"role": "user", "content": current_prompt}]
            )
            raw_text = res.content[0].text

            try:
                clean_dict = sanitizer.sanitize(raw_text)
                return target_schema.model_validate(clean_dict)
            except (json.JSONDecodeError, ValidationError) as err:
                if attempt == self.max_retries:
                    raise err

                # Formulate surgical repair prompt
                error_details = str(err)
                print(f"⚠️ Validation error on attempt {attempt+1}. Formulating surgical repair: {error_details[:100]}...")
                current_prompt = (
                    f"Your previous JSON output was INVALID.\n\n"
                    f"PREVIOUS OUTPUT:\n{raw_text}\n\n"
                    f"VALIDATION ERROR DETAILS:\n{error_details}\n\n"
                    "Fix ONLY the validation errors noted above and emit the corrected JSON object."
                )

        raise RuntimeError("Unreachable state in schema repair runner.")
