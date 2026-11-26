import { test, expect } from "vitest";
import { Spectral } from "@stoplight/spectral-core";
import { oas } from "@stoplight/spectral-rulesets";
import fs from "fs";
import yaml from "js-yaml";

test("OpenAPI schema passes EAAIS-2026 enterprise compliance audit", async () => {
  const fileContent = fs.readFileSync("./openapi_action_spec.yaml", "utf8");
  const parsedSpec = yaml.load(fileContent);

  const spectral = new Spectral();
  spectral.setRuleset(await import("./.spectral.yaml"));

  const results = await spectral.run(parsedSpec);
  const criticalErrors = results.filter((r) => r.severity === 0);

  expect(criticalErrors.length).toBe(0);
});
