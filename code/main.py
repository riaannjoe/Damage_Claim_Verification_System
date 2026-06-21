import os
import json
import time
from pathlib import Path
from typing import List, Literal
import pandas as pd
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# DATA LOADING

BASE_DIR = Path(__file__).resolve().parent
print("main.py folder:", BASE_DIR)

# LOAD CLAIMS


claims_path = BASE_DIR.parent.parent / "dataset" / "claims.csv"
print("Claims path:", claims_path)

claims = pd.read_csv(claims_path)

# Clean column names
claims.columns = (
    claims.columns
    .str.strip()
    .str.replace('"', '', regex=False)
)

print(claims.head())
print(f"Total claims: {len(claims)}")


# USER HISTORY


def get_user_history(user_id, history_df):
    user_row = history_df[
        history_df["user_id"] == str(user_id)
    ]
    if len(user_row) == 0:
        return None
    return user_row.iloc[0]


history_path = (
    BASE_DIR.parent.parent
    / "dataset"
    / "user_history.csv"
)

history = pd.read_csv(history_path)

# Clean columns
history.columns = (
    history.columns
    .str.strip()
    .str.replace('"', '', regex=False)
)

# Clean values
history = history.apply(
    lambda col: col.str.replace('"', '', regex=False).str.strip()
    if col.dtype == "object"
    else col
)

print("\nHISTORY COLUMNS")
print(history.columns.tolist())


# IMAGE IDS


def get_image_ids(image_paths):
    image_list = image_paths.split(";")
    image_ids = []
    for image in image_list:
        image_id = Path(image).stem
        image_ids.append(image_id)
    return image_ids


print("\nIMAGE IDS")



# DAMAGE KEYWORDS


def extract_damage_keywords(claim_text):
    claim_text = claim_text.lower()
    keywords = []
    possible_parts = [
        "bumper", "headlight", "windshield", "mirror", "door", "hood", 
        "taillight", "screen", "keyboard", "trackpad", "hinge", "lid", 
        "corner", "label", "seal", "contents"
    ]
    for part in possible_parts:
        if part in claim_text:
            keywords.append(part)
    return list(set(keywords))



# EVIDENCE REQUIREMENTS


requirements_path = (
    BASE_DIR.parent.parent
    / "dataset"
    / "evidence_requirements.csv"
)

requirements = pd.read_csv(requirements_path)

requirements.columns = (
    requirements.columns
    .str.strip()
    .str.replace('"', '', regex=False)
)

print("\nEVIDENCE REQUIREMENTS")
print(requirements.head())



# REQUIREMENT MATCHING


def get_relevant_requirements(
    claim_object,
    damage_keywords,
    requirements_df
):
    relevant = []
    for _, row in requirements_df.iterrows():
        applies_to_object = str(row["claim_object"]).lower()
        applies_text = str(row["applies_to"]).lower()

        # Rules that apply to everything
        if applies_to_object == "all":
            relevant.append(row["requirement_id"])
            continue

        # Rules for this object type
        if applies_to_object == claim_object.lower():
            for keyword in damage_keywords:
                if keyword in applies_text:
                    relevant.append(row["requirement_id"])
                    break
    return list(set(relevant))



# Image evidence path


def get_full_image_paths(image_paths):
    full_paths = []
    for image_path in image_paths.split(";"):
        full_path = (
            BASE_DIR.parent.parent
            / "dataset"
            / image_path.strip()
        )
        full_paths.append(full_path)
    return full_paths


print("\nFULL IMAGE PATHS")

# GEMINI STRUCTURING & INITIALIZATION 

env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

class ClaimAnalysisOutput(BaseModel):
    evidence_standard_met: bool = Field(description="true if image set contains enough visual context to evaluate the text claim, else false")
    evidence_standard_met_reason: str = Field(description="Short sentence explanation justifying the standard determination")
    risk_flags: List[Literal[
        'none', 'blurry_image', 'cropped_or_obstructed', 'low_light_or_glare', 
        'wrong_angle', 'wrong_object', 'wrong_object_part', 'damage_not_visible', 
        'claim_mismatch', 'possible_manipulation', 'non_original_image', 
        'text_instruction_present', 'manual_review_required'
    ]] = Field(description="Array of visual discrepancies caught in images")
    issue_type: Literal[
        'dent', 'scratch', 'crack', 'glass_shatter', 'broken_part', 'missing_part', 
        'torn_packaging', 'crushed_packaging', 'water_damage', 'stain', 'none', 'unknown'
    ]
    object_part: str = Field(description="Specific part matching allowed lists or unknown")
    claim_status: Literal['supported', 'contradicted', 'not_enough_information']
    claim_status_justification: str = Field(description="Concise evidence explanation referencing image identifiers")
    supporting_image_ids: List[str] = Field(description="List of filenames without extension, or ['none']")
    valid_image: bool = Field(description="true if images are completely readable and clean, else false")
    severity: Literal['none', 'low', 'medium', 'high', 'unknown']



# UPDATED FULL PROCESS PIPELINE WITH RETRIES


def process_claim(claim):
    user_history = get_user_history(claim["user_id"], history)
    damage_keywords = extract_damage_keywords(claim["user_claim"])
    relevant_requirements = get_relevant_requirements(
        claim["claim_object"],
        damage_keywords,
        requirements
    )
    full_image_paths = get_full_image_paths(claim["image_paths"])

    # Load images and build operational text manifests
    loaded_images = []
    image_manifest = []
    for p in full_image_paths:
        if p.exists():
            try:
                loaded_images.append(Image.open(p))
                image_manifest.append(f"Image File ID: {p.stem}")
            except Exception:
                pass

    if not loaded_images:
        return {
            "evidence_standard_met": "false", "evidence_standard_met_reason": "No image files present.",
            "risk_flags": "none", "issue_type": "none", "object_part": "unknown",
            "claim_status": "not_enough_information", "claim_status_justification": "Missing evidence.",
            "supporting_image_ids": "none", "valid_image": "false", "severity": "none"
        }, 0, 0, 0.0

    # Format pipeline requirements text
    reqs_text = ", ".join(relevant_requirements) if relevant_requirements else "General review standard applies"
    history_risk = "none"
    if user_history is not None:
        history_risk = str(user_history.get("history_flags", "none")).strip().lower()

    # System operational prompt context
    prompt = f"""
    You are an automated claims compliance reviewer verifying user claims using multimodal proof.
    Review the images to see if they back up the user claim text transcript.
    
    Claim Object Type: {claim["claim_object"]}
    User Claim Statement: "{claim['user_claim']}"
    
    Visual Mapping Context:
    {chr(10).join(image_manifest)}
    
    Applicable System Rule Requirements: {reqs_text}
    Customer Background Metadata Risk: {history_risk}
    """

    t0 = time.time()
    
    # Robust multi-attempt loop to absorb rate limit shocks
    max_attempts = 5
    backoff_delay = 12
    
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=loaded_images + [prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClaimAnalysisOutput,
                    temperature=0.1
                )
            )
            latency = time.time() - t0
            raw_res = json.loads(response.text)
            
            # 1. Normalize boolean fields to exactly match lowercase grading expectations
            ev_met = "true" if raw_res.get("evidence_standard_met") is True else "false"
            v_img = "true" if raw_res.get("valid_image") is True else "false"

            # 2. Extract and format Risk Flags cleanly
            r_flags = raw_res.get("risk_flags", [])
            if not isinstance(r_flags, list):
                r_flags = [str(r_flags)]
            
            # Incorporate profile risk flag into column string securely if flagged
            if "none" not in history_risk and "user_history_risk" not in r_flags:
                r_flags.append("user_history_risk")
                
            # Sanitize array items
            r_flags = [str(f).strip() for f in r_flags if str(f).strip() != ""]
            if not r_flags or r_flags == ["none"]:
                r_flags_str = "none"
            else:
                if "none" in r_flags and len(r_flags) > 1:
                    r_flags.remove("none")
                r_flags_str = ";".join(r_flags)

            # 3. Extract and format Supporting Image Identifiers cleanly
            img_ids = raw_res.get("supporting_image_ids", ["none"])
            if not isinstance(img_ids, list):
                img_ids = [str(img_ids)]
            img_ids = [str(i).strip() for i in img_ids if str(i).strip() != ""]
            img_ids_str = ";".join(img_ids) if img_ids else "none"

            return {
                "evidence_standard_met": ev_met,
                "evidence_standard_met_reason": str(raw_res.get("evidence_standard_met_reason", "")),
                "risk_flags": r_flags_str,
                "issue_type": str(raw_res.get("issue_type", "unknown")),
                "object_part": str(raw_res.get("object_part", "unknown")),
                "claim_status": str(raw_res.get("claim_status", "not_enough_information")),
                "claim_status_justification": str(raw_res.get("claim_status_justification", "")),
                "supporting_image_ids": img_ids_str,
                "valid_image": v_img,
                "severity": str(raw_res.get("severity", "unknown"))
            }, response.usage_metadata.prompt_token_count, response.usage_metadata.candidates_token_count, latency

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"   [Rate Limit Warning] Free tier threshold hit. Sleeping {backoff_delay}s before retry (Attempt {attempt + 1}/{max_attempts})...")
                time.sleep(backoff_delay)
                backoff_delay *= 1.5  # Progressive backoff cooling
                continue
            
            print(f"Loop API execution error: {e}")
            break

    # Final error fallback
    return {
        "evidence_standard_met": "false", "evidence_standard_met_reason": "API execution failure fallback.",
        "risk_flags": "manual_review_required", "issue_type": "unknown", "object_part": "unknown",
        "claim_status": "not_enough_information", "claim_status_justification": "API Quota limit fallback.",
        "supporting_image_ids": "none", "valid_image": "false", "severity": "unknown"
    }, 0, 0, time.time() - t0



# BATCH PROCESSING


all_results = []
metric_prompt_tokens = 0
metric_completion_tokens = 0
metric_total_time = 0
processed_images_count = 0

for index, claim in claims.iterrows():
    print(f"Processing Claim {index + 1}/{len(claims)}")
    processed_images_count += len(claim["image_paths"].split(";"))
    
    result, in_t, out_t, lat = process_claim(claim)
    
    metric_prompt_tokens += in_t
    metric_completion_tokens += out_t
    metric_total_time += lat

    # Combine input metadata with VLM results
    output_row = {
        "user_id": claim["user_id"],
        "image_paths": claim["image_paths"],
        "user_claim": claim["user_claim"],
        "claim_object": claim["claim_object"],
        **result
    }
    all_results.append(output_row)
    
    # Mild baseline spacing delay to satisfy standard free tier windows safely
    time.sleep(4.5)

# RESULTS DATAFRAME


results_df = pd.DataFrame(all_results)
print("\nRESULTS DATAFRAME")
print(results_df.head())


# SAVE RESULTS 


output_path = BASE_DIR.parent.parent / "output.csv"
results_df.to_csv(output_path, index=False)
print("\nSaved output mapping safely directly to:", output_path)


# FINAL RESULT

print("\n" + "="*40)
print("METRICS FOR EVALUATION REPORT")
print("="*40)
print(f"Total Claims Analyzed: {len(claims)}")
print(f"Total System Images Parsed: {processed_images_count}")
print(f"Accumulated Input Tokens: {metric_prompt_tokens}")
print(f"Accumulated Output Tokens: {metric_completion_tokens}")
print(f"Total Execution Latency: {metric_total_time:.2f} seconds")
est_cost = ((metric_prompt_tokens / 1_000_000) * 0.075) + ((metric_completion_tokens / 1_000_000) * 0.30)
print(f"Estimated Operational Pipeline Financial Cost: ${est_cost:.6f}")
print("="*40)
