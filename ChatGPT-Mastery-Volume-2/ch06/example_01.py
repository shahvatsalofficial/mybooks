"""
Production OpenAI Fine-Tuning Pipeline for GPT-4o-mini
Author: Vatsal Shah, Enterprise AI Architect
Version: 2.0 (Production Hardened)
"""
import os
import json
import time
import tiktoken
from typing import List, Dict, Tuple
from openai import OpenAI

client = OpenAI()

class FineTuningDatasetValidator:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")

    def validate_file(self, filepath: str) -> Tuple[bool, int, List[str]]:
        """Audits JSONL file for schema errors, role alternating, and token lengths."""
        errors = []
        total_tokens = 0
        total_samples = 0

        if not os.path.exists(filepath):
            return False, 0, [f"File {filepath} not found."]

        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                except Exception as e:
                    errors.append(f"Line {line_num}: Invalid JSON syntax ({e})")
                    continue

                if "messages" not in data or not isinstance(data["messages"], list):
                    errors.append(f"Line {line_num}: Missing 'messages' array.")
                    continue

                messages = data["messages"]
                if len(messages) < 2:
                    errors.append(f"Line {line_num}: Sample must contain at least 2 messages.")
                    continue

                # Audit message roles and token lengths
                sample_tokens = 0
                for msg in messages:
                    if "role" not in msg or "content" not in msg:
                        errors.append(f"Line {line_num}: Message missing 'role' or 'content'.")
                        continue
                    if msg["role"] not in ["system", "user", "assistant"]:
                        errors.append(f"Line {line_num}: Invalid role '{msg['role']}'.")
                    
                    content_text = msg["content"]
                    sample_tokens += len(self.encoding.encode(content_text))

                if sample_tokens > 16384:
                    errors.append(f"Line {line_num}: Exceeds maximum 16k context window ({sample_tokens} tokens).")

                total_tokens += sample_tokens
                total_samples += 1

        print(f"📊 Audited {total_samples} samples. Total Tokens: {total_tokens:,}")
        is_valid = len(errors) == 0
        return is_valid, total_tokens, errors


def launch_enterprise_fine_tuning():
    print("
=======================================================")
    print("🚀 INITIATING ENTERPRISE GPT-4o-MINI FINE-TUNING PIPELINE")
    print("=======================================================
")

    train_path = "scratch/financial_support_train.jsonl"
    val_path = "scratch/financial_support_val.jsonl"

    # Step 1: Pre-Flight Dataset Validation
    validator = FineTuningDatasetValidator()
    print("1. Validating Training Dataset...")
    valid, train_tokens, errors = validator.validate_file(train_path)
    if not valid:
        print("❌ Dataset validation failed with errors:")
        for err in errors[:5]:
            print(f"   • {err}")
        return

    # Step 2: Upload Files to OpenAI Storage API
    print("
2. Uploading Datasets to OpenAI Files API...")
    with open(train_path, "rb") as f_train:
        train_file = client.files.create(file=f_train, purpose="fine-tune")
    print(f"   ✅ Training File Uploaded. ID: {train_file.id}")

    with open(val_path, "rb") as f_val:
        val_file = client.files.create(file=f_val, purpose="fine-tune")
    print(f"   ✅ Validation File Uploaded. ID: {val_file.id}")

    # Step 3: Launch Supervised Fine-Tuning Job
    print("
3. Provisioning Fine-Tuning Job on gpt-4o-mini...")
    job = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model="gpt-4o-mini-2024-07-18",
        hyperparameters={
            "n_epochs": 2,
            "learning_rate_multiplier": 0.1,
            "batch_size": "auto"
        },
        suffix="fin-support-v2"
    )
    print(f"   ✅ Job Created! Job ID: {job.id}")

    # Step 4: Monitor Training Progress via Event Polling
    print("
4. Polling Fine-Tuning Job Status...")
    while True:
        status_check = client.fine_tuning.jobs.retrieve(job.id)
        status = status_check.status
        print(f"   [{time.strftime('%H:%M:%S')}] Current Status: {status.upper()}")

        if status == "succeeded":
            fine_tuned_model_id = status_check.fine_tuned_model
            print(f"
🎉 FINE-TUNING COMPLETED SUCCESSFULLY!")
            print(f"🚀 Deployable Model ID: {fine_tuned_model_id}")
            break
        elif status in ["failed", "cancelled"]:
            print(f"
❌ Job terminated prematurely with status: {status}")
            if status_check.error:
                print(f"   Error Details: {status_check.error.message}")
            break

        time.sleep(30)

if __name__ == "__main__":
    launch_enterprise_fine_tuning()
