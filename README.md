# Damage Claim Verification System

## Overview

This project is an AI-powered **multimodal insurance claim verification pipeline** that analyzes customer-submitted claims using both:

* **Textual claim descriptions**
* **Uploaded image evidence**

The system automatically evaluates whether the provided images sufficiently support the user’s damage claim and flags suspicious or insufficient evidence for manual review.

It uses **Google Gemini 2.5 Flash Vision** for multimodal reasoning and outputs a structured claim assessment.

---

## Problem Statement

Insurance and warranty claim verification is often slow and manual. Fraudulent or low-quality claims increase operational costs and delay genuine approvals.

This system helps automate the initial verification process by answering:

* Is the image evidence sufficient?
* Does the visual damage match the written claim?
* Are there signs of fraud or manipulation?
* Should the claim be escalated for manual review?

---

## Features

### 1. Claim Data Processing

Loads and cleans structured claim data from CSV files:

* `claims.csv`
* `user_history.csv`
* `evidence_requirements.csv`

Data cleaning includes:

* Removing quotes
* Stripping whitespace
* Standardizing column names

---

### 2. Damage Keyword Extraction

The system extracts relevant damage-related object parts from claim text.

Supported keywords include:

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
User claim:

> "My laptop screen cracked near the hinge"

Extracted keywords:

* screen
* hinge

---

### 3. Evidence Requirement Matching

Each claim is matched with predefined verification rules from `evidence_requirements.csv`.

Example rules:

* Full object visibility required
* Damage area must be clearly visible
* Multiple viewing angles required

Requirements are selected based on:

* Claim object type
* Damage location keywords

---

### 4. Image Evidence Loading

The system loads all submitted images from dataset folders.

Supported behavior:

* Multi-image claims
* Missing file handling
* Invalid image fallback
* Image ID extraction from filenames

Example:
damage_001.jpg → image ID = `damage_001`

---

### 5. Multimodal AI Analysis (Gemini)

The core reasoning engine uses:

**Google Gemini 2.5 Flash**

Inputs:

* Claim text
* Image evidence
* User fraud history
* Required evidence rules

Gemini performs:

* Visual inspection
* Claim verification
* Risk detection
* Damage classification

---

## AI Output Schema

The model returns structured JSON with:

### Evidence Quality

* `evidence_standard_met`
* `evidence_standard_met_reason`

Determines whether enough evidence exists.

---

### Risk Flags

Possible risk flags:

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

Possible issue types:

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

Possible outputs:

* `supported`
* `contradicted`
* `not_enough_information`

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

Detects:

* suspicious edits
* inconsistent damage
* mismatched object claims
* manipulated images

### Historical Risk Detection

User history is analyzed using:

* prior fraud flags
* suspicious claim patterns

If user history contains risk markers:

* `user_history_risk` is appended to output flags

---

## Retry & Rate Limit Handling

Since Gemini free-tier APIs may return rate-limit errors (`429 RESOURCE_EXHAUSTED`), the pipeline includes:

* Automatic retries
* Progressive exponential backoff
* Failure-safe fallback response

Retry settings:

* Max attempts: 5
* Initial backoff: 12 seconds
* Backoff multiplier: 1.5×

This improves reliability for batch processing.

---

## Batch Processing Pipeline

For every claim:

1. Load claim
2. Fetch user history
3. Extract damage keywords
4. Match evidence requirements
5. Load images
6. Send multimodal prompt to Gemini
7. Parse structured JSON response
8. Save results

---

## Output Format

Results are saved to:

`output.csv`

Each row contains:

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

The system tracks operational metrics:

* Total claims processed
* Total images analyzed
* Input tokens used
* Output tokens generated
* Total latency
* Estimated API cost

Example:

* Prompt tokens: 120,000
* Completion tokens: 25,000
* Latency: 48.3s
* Estimated cost: $0.016

---

## Tech Stack

### Programming

* Python 3.x

### Libraries

* pandas
* Pillow
* pathlib
* dotenv
* pydantic

### AI Model

* Google Gemini 2.5 Flash Vision

---

## Project Structure

```bash
project/
│
├── src/
│   └── main.py
│
├── dataset/
│   ├── claims.csv
│   ├── user_history.csv
│   ├── evidence_requirements.csv
│   └── images/
│
├── output.csv
├── .env
└── README.md
```

---

## Setup Instructions

### 1. Clone Repository

```bash
git clone <repository_url>
cd project
```

### 2. Install Dependencies

```bash
pip install pandas pillow python-dotenv pydantic google-genai
```

### 3. Configure Environment Variables

Create `.env`

```env
GEMINI_API_KEY=your_api_key_here
```

### 4. Run

```bash
python main.py
```

---

## Example Use Case

### Input Claim

```text
Claim Object: car
Claim: Front bumper dent after collision
Images: 3 uploaded photos
```

### AI Output

```json
{
  "evidence_standard_met": "true",
  "risk_flags": "none",
  "issue_type": "dent",
  "object_part": "bumper",
  "claim_status": "supported",
  "severity": "medium"
}
```

---

## Future Improvements

Potential enhancements:

* Fraud scoring model
* Human-in-the-loop review dashboard
* Fine-tuned domain-specific VLM
* Real-time web deployment
* OCR for invoice validation
* Image tampering detection using CV models

---

## Conclusion

This system demonstrates how **Vision Language Models (VLMs)** can automate claim verification by combining image understanding, textual reasoning, and fraud detection.

It reduces manual workload, improves consistency, and helps prioritize suspicious claims for human review.
