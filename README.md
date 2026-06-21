# Multi-Modal Damage Claim Verification System

## Overview

An AI-powered multimodal claim verification system that combines image understanding, claim text analysis, evidence requirements, and user history to determine whether a damage claim is supported, contradicted, or lacks sufficient evidence.

Built using **Google Gemini 2.5 Flash Vision** as part of the **HackerRank Orchestrate Hackathon**.

The system automates the initial stages of insurance and warranty claim verification, helping reduce manual workload and prioritize suspicious claims for human review.

---

## Problem Statement

Insurance and warranty claim verification is often time-consuming and manually intensive.

Fraudulent, incomplete, or low-quality claims can:

* Increase operational costs
* Delay legitimate claim approvals
* Create inconsistencies in decision-making

This project automates the initial verification process by answering:

* Does the image evidence support the written claim?
* Is the reported damage visible?
* Are the provided images sufficient?
* Are there indicators of fraud or manipulation?
* Should the claim be escalated for manual review?

---

## System Architecture

```text
Claim Data
     │
     ▼
Keyword Extraction
     │
     ▼
Evidence Requirement Matching
     │
     ▼
Image Loading & Validation
     │
     ▼
Gemini 2.5 Flash Vision
     │
     ▼
Structured Claim Assessment
     │
     ▼
Output CSV
```

---

## Features

### Claim Data Processing

Loads and cleans structured claim data from:

* claims.csv
* user_history.csv
* evidence_requirements.csv

Cleaning includes:

* Removing quotes
* Trimming whitespace
* Standardizing column names

---

### Damage Keyword Extraction

Extracts relevant object parts and damage locations from user claims.

Supported examples include:

* bumper
* headlight
* windshield
* mirror
* door
* hood
* screen
* keyboard
* hinge
* lid
* packaging-related terms

Example:

**Claim**

```text
My laptop screen cracked near the hinge
```

**Extracted Keywords**

```text
screen
hinge
```

---

### Evidence Requirement Matching

Each claim is matched against predefined verification rules.

Examples:

* Full object visibility required
* Damage area must be clearly visible
* Multiple viewing angles required

Requirements are selected based on:

* Claim object type
* Damage location keywords

---

### Image Evidence Processing

Supports:

* Multi-image claims
* Missing image handling
* Invalid image fallback
* Image ID extraction

Example:

```text
damage_001.jpg → damage_001
```

---

### Multimodal AI Analysis

The core reasoning engine uses:

**Google Gemini 2.5 Flash Vision**

Inputs:

* Claim description
* Uploaded images
* User fraud history
* Evidence requirements

The model performs:

* Visual inspection
* Claim verification
* Risk assessment
* Damage classification
* Evidence validation

---

## AI Output Schema

### Evidence Quality

Determines whether sufficient evidence exists.

Fields:

* evidence_standard_met
* evidence_standard_met_reason

---

### Risk Flags

Possible flags include:

* none
* blurry_image
* cropped_or_obstructed
* low_light_or_glare
* wrong_angle
* wrong_object
* wrong_object_part
* damage_not_visible
* claim_mismatch
* possible_manipulation
* non_original_image
* text_instruction_present
* manual_review_required

---

### Damage Classification

Possible outputs:

* dent
* scratch
* crack
* glass_shatter
* broken_part
* missing_part
* torn_packaging
* crushed_packaging
* water_damage
* stain
* none
* unknown

---

### Claim Status

Possible outcomes:

* supported
* contradicted
* not_enough_information

---

### Severity Levels

* none
* low
* medium
* high
* unknown

---

## Fraud Detection Logic

The system combines:

### Visual Risk Detection

Identifies:

* Suspicious edits
* Inconsistent damage
* Mismatched claim evidence
* Potential image manipulation

### Historical Risk Detection

Analyzes user history using:

* Prior fraud flags
* Suspicious claim patterns

If risk indicators exist, the system appends:

```text
user_history_risk
```

to the output flags.

---

## Rate Limit & Retry Handling

Gemini free-tier APIs may occasionally return:

```text
429 RESOURCE_EXHAUSTED
```

To improve reliability, the pipeline includes:

* Automatic retries
* Progressive exponential backoff
* Failure-safe fallback responses

Configuration:

* Maximum attempts: 5
* Initial backoff: 12 seconds
* Backoff multiplier: 1.5×

---

## Processing Pipeline

For every claim:

1. Load claim information
2. Fetch user history
3. Extract damage keywords
4. Match evidence requirements
5. Load and validate images
6. Send multimodal prompt to Gemini
7. Parse structured JSON response
8. Save results to output file

---

## Output Format

Results are saved to:

```text
output.csv
```

### Input Fields

* user_id
* image_paths
* user_claim
* claim_object

### AI Output Fields

* evidence_standard_met
* evidence_standard_met_reason
* risk_flags
* issue_type
* object_part
* claim_status
* claim_status_justification
* supporting_image_ids
* valid_image
* severity

---

## Evaluation Metrics

The system tracks:

* Total claims processed
* Total images analyzed
* Input tokens used
* Output tokens generated
* Total latency
* Estimated API cost

Example:

```text
Prompt Tokens: 120,000
Completion Tokens: 25,000
Latency: 48.3 seconds
Estimated Cost: $0.016
```

---

## Tech Stack

### Programming Language

* Python 3.x

### Libraries

* pandas
* Pillow
* python-dotenv
* pydantic
* google-genai

### AI Model

* Google Gemini 2.5 Flash Vision

---

## Project Structure

```text
Damage_Claim_Verification_System/
│
├── code/
│   └── main.py
│   └── .env.example
|
├── dataset/
│   ├── claims.csv
|   ├── sample_claims.csv
│   ├── user_history.csv
│   ├── evidence_requirements.csv
│   └── images/
│
├── output.csv
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone <repository_url>
cd Damage_Claim_Verification_System
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file using `.env.example`:

```env
GEMINI_API_KEY=your_api_key_here
```

### Run

```bash
python code/main.py
```

---

## Example Use Case

### Input

```text
Claim Object: Car

Claim:
Front bumper dent after collision

Images:
3 uploaded photos
```

### Output

```json
{
  "evidence_standard_met": true,
  "risk_flags": ["none"],
  "issue_type": "dent",
  "object_part": "bumper",
  "claim_status": "supported",
  "severity": "medium"
}
```

---

## Future Improvements

Potential enhancements include:

* Fraud scoring models
* Human-in-the-loop review dashboard
* Fine-tuned domain-specific vision-language models
* Real-time web deployment
* OCR-based invoice validation
* Image tampering detection using computer vision techniques

---

## Conclusion

This project demonstrates how Vision Language Models (VLMs) can automate claim verification by combining image understanding, textual reasoning, evidence validation, and fraud detection.

By leveraging multimodal AI, the system helps reduce manual workload, improve consistency, and prioritize suspicious claims for human review.
