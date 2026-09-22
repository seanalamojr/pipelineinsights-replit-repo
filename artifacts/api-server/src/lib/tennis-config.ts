import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function configPathCandidates(): string[] {
  return [
    resolve(process.cwd(), "config/tennis.yaml"),
    resolve(process.cwd(), "../../config/tennis.yaml"),
  ];
}

export function readValueEdgeThreshold(): number {
  const configPath = configPathCandidates().find((candidate) => {
    try {
      readFileSync(candidate, "utf8");
      return true;
    } catch {
      return false;
    }
  });
  if (!configPath) {
    throw new Error("config/tennis.yaml is required for API thresholds");
  }

  const configText = readFileSync(configPath, "utf8");
  const match = configText.match(
    /^value_edge_threshold:\s*([0-9]+(?:\.[0-9]+)?)\s*$/m,
  );
  const threshold = match ? Number(match[1]) : Number.NaN;
  if (!Number.isFinite(threshold) || threshold <= 0) {
    throw new Error(
      "config/tennis.yaml must define a positive value_edge_threshold",
    );
  }
  return threshold;
}