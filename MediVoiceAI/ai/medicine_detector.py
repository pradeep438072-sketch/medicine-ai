"""
MediVoice AI - Medicine Detector and Clinical Knowledge Base
"""

import re

# Comprehensive real-world medicine database
MEDICINE_DATABASE = {
    "paracetamol": {
        "name": "Paracetamol",
        "generic_name": "Acetaminophen",
        "category": "Analgesic & Antipyretic (Pain & Fever)",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "4000 mg (8 tablets) / 24 hours",
        "frequency": "Every 6 to 8 hours as needed",
        "doses_per_day": 3,
        "suggested_usage": "Take with or without food. Do not exceed 4g daily to avoid liver toxicity.",
        "warnings": "Avoid alcohol. Check for other combination products containing acetaminophen."
    },
    "acetaminophen": {
        "name": "Acetaminophen",
        "generic_name": "Paracetamol",
        "category": "Analgesic & Antipyretic",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "4000 mg / 24 hours",
        "frequency": "Every 6 hours",
        "doses_per_day": 3,
        "suggested_usage": "Take with a glass of water.",
        "warnings": "Do not take with other acetaminophen products."
    },
    "amoxicillin": {
        "name": "Amoxicillin",
        "generic_name": "Amoxicillin Trihydrate",
        "category": "Antibiotic (Penicillin class)",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "1500 mg (3 doses) / day",
        "frequency": "Every 8 hours",
        "doses_per_day": 3,
        "suggested_usage": "Take at the start of a light meal to reduce stomach upset. Complete full course.",
        "warnings": "Contraindicated if allergic to penicillin or beta-lactam antibiotics."
    },
    "ibuprofen": {
        "name": "Ibuprofen",
        "generic_name": "Ibuprofen",
        "category": "NSAID (Anti-inflammatory)",
        "default_dosage": "400",
        "unit": "mg",
        "limit": "1200 mg OTC (2400 mg prescription) / day",
        "frequency": "Every 6 to 8 hours",
        "doses_per_day": 3,
        "suggested_usage": "Always take after food or milk to prevent gastric irritation.",
        "warnings": "Caution with history of peptic ulcers or kidney disease."
    },
    "metformin": {
        "name": "Metformin",
        "generic_name": "Metformin Hydrochloride",
        "category": "Antidiabetic (Biguanide)",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "2000 mg / day",
        "frequency": "Twice daily with meals",
        "doses_per_day": 2,
        "suggested_usage": "Take with breakfast and dinner to lessen gastrointestinal side effects.",
        "warnings": "Periodic renal function monitoring recommended."
    },
    "atorvastatin": {
        "name": "Atorvastatin",
        "generic_name": "Atorvastatin Calcium",
        "category": "Statin (Cholesterol lowering)",
        "default_dosage": "20",
        "unit": "mg",
        "limit": "80 mg / day",
        "frequency": "Once daily at bedtime",
        "doses_per_day": 1,
        "suggested_usage": "Take once a day in the evening with or without food.",
        "warnings": "Avoid excessive grapefruit juice consumption."
    },
    "cetirizine": {
        "name": "Cetirizine",
        "generic_name": "Cetirizine Hydrochloride",
        "category": "Antihistamine (Allergy relief)",
        "default_dosage": "10",
        "unit": "mg",
        "limit": "10 mg (1 tablet) / day",
        "frequency": "Once daily",
        "doses_per_day": 1,
        "suggested_usage": "May be taken in evening if drowsiness occurs.",
        "warnings": "Use caution when operating machinery or driving."
    },
    "omeprazole": {
        "name": "Omeprazole",
        "generic_name": "Omeprazole Magnesium",
        "category": "Proton Pump Inhibitor (Antacid / GERD)",
        "default_dosage": "20",
        "unit": "mg",
        "limit": "40 mg / day",
        "frequency": "Once daily in the morning",
        "doses_per_day": 1,
        "suggested_usage": "Swallow whole 30-60 minutes before breakfast.",
        "warnings": "Do not chew or crush delayed-release capsules."
    },
    "pantoprazole": {
        "name": "Pantoprazole",
        "generic_name": "Pantoprazole Sodium",
        "category": "Proton Pump Inhibitor (Acid Reflux)",
        "default_dosage": "40",
        "unit": "mg",
        "limit": "80 mg / day",
        "frequency": "Once daily before breakfast",
        "doses_per_day": 1,
        "suggested_usage": "Take 30 minutes before first meal of the day.",
        "warnings": "Swallow tablets whole with water."
    },
    "azithromycin": {
        "name": "Azithromycin",
        "generic_name": "Azithromycin Dihydrate",
        "category": "Antibiotic (Macrolide)",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "500 mg / day",
        "frequency": "Once daily for 3 to 5 days",
        "doses_per_day": 1,
        "suggested_usage": "Can be taken with or without food. Take at the same time each day.",
        "warnings": "Complete prescribed duration even if feeling better."
    },
    "losartan": {
        "name": "Losartan",
        "generic_name": "Losartan Potassium",
        "category": "Antihypertensive (ARB)",
        "default_dosage": "50",
        "unit": "mg",
        "limit": "100 mg / day",
        "frequency": "Once daily in morning",
        "doses_per_day": 1,
        "suggested_usage": "Take with or without food at regular intervals.",
        "warnings": "Avoid potassium supplements without doctor consultation."
    },
    "ciprofloxacin": {
        "name": "Ciprofloxacin",
        "generic_name": "Ciprofloxacin Hydrochloride",
        "category": "Fluoroquinolone Antibiotic",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "1000 mg / day",
        "frequency": "Every 12 hours",
        "doses_per_day": 2,
        "suggested_usage": "Drink plenty of fluids. Avoid taking with dairy or calcium-fortified products.",
        "warnings": "Report any sudden joint or tendon discomfort immediately."
    },
    "aspirin": {
        "name": "Aspirin",
        "generic_name": "Acetylsalicylic Acid",
        "category": "Antiplatelet / Pain Reliever",
        "default_dosage": "81",
        "unit": "mg",
        "limit": "325 mg / day (cardiac prophylaxis)",
        "frequency": "Once daily",
        "doses_per_day": 1,
        "suggested_usage": "Take with food and full glass of water.",
        "warnings": "Consult physician if taking blood thinners or before surgery."
    },
    "vitamin c": {
        "name": "Vitamin C",
        "generic_name": "Ascorbic Acid",
        "category": "Dietary Supplement / Vitamin",
        "default_dosage": "500",
        "unit": "mg",
        "limit": "2000 mg / day",
        "frequency": "Once or twice daily",
        "doses_per_day": 1,
        "suggested_usage": "Take after meals. Chewable or effervescent with water.",
        "warnings": "High doses may cause mild gastrointestinal distress."
    },
    "vitamin d3": {
        "name": "Vitamin D3",
        "generic_name": "Cholecalciferol",
        "category": "Dietary Supplement / Bone Health",
        "default_dosage": "1000",
        "unit": "IU",
        "limit": "4000 IU / day",
        "frequency": "Once daily",
        "doses_per_day": 1,
        "suggested_usage": "Best absorbed when taken with a meal containing healthy fats.",
        "warnings": "Do not exceed prescribed high-dose weekly regimens."
    },
    "montelukast": {
        "name": "Montelukast",
        "generic_name": "Montelukast Sodium",
        "category": "Leukotriene Receptor Antagonist (Asthma / Allergy)",
        "default_dosage": "10",
        "unit": "mg",
        "limit": "10 mg / day",
        "frequency": "Once daily in evening",
        "doses_per_day": 1,
        "suggested_usage": "Take in the evening with or without food.",
        "warnings": "Not indicated for the relief of acute asthma attacks."
    },
    "amlodipine": {
        "name": "Amlodipine",
        "generic_name": "Amlodipine Besylate",
        "category": "Calcium Channel Blocker (Blood Pressure)",
        "default_dosage": "5",
        "unit": "mg",
        "limit": "10 mg / day",
        "frequency": "Once daily",
        "doses_per_day": 1,
        "suggested_usage": "Take consistently at the same time each day.",
        "warnings": "Check blood pressure periodically."
    }
}

# Symptom-to-guidance knowledge base
SYMPTOM_SUGGESTIONS = [
    {
        "keywords": ["headache", "head pain", "migraine", "fever", "body ache", "temperature"],
        "condition": "Mild Pain or Fever",
        "general_medicines": ["Paracetamol (500 mg)", "Ibuprofen (400 mg)"],
        "home_care": "Rest in a quiet, dark room, stay hydrated with plenty of water, and apply a cool or warm compress to forehead.",
        "when_to_see_doctor": "Seek emergency medical care if accompanied by stiff neck, confusion, high fever over 103°F (39.4°C), or sudden severe 'thunderclap' headache."
    },
    {
        "keywords": ["cough", "cold", "runny nose", "sneezing", "congestion", "sore throat"],
        "condition": "Common Cold or Upper Respiratory Irritation",
        "general_medicines": ["Cetirizine (10 mg) for allergic rhinitis", "Warm saline gargle", "Vitamin C (500 mg)"],
        "home_care": "Steam inhalation, warm honey-lemon tea, saline nasal spray, and adequate rest.",
        "when_to_see_doctor": "Consult a doctor if cough lasts longer than 2 weeks, produces blood or rust-colored phlegm, or causes difficulty breathing."
    },
    {
        "keywords": ["acidity", "acid reflux", "heartburn", "gastric", "stomach burn", "indigestion", "gerd"],
        "condition": "Acid Indigestion or Gastroesophageal Reflux",
        "general_medicines": ["Omeprazole (20 mg)", "Pantoprazole (40 mg)", "Antacid suspension"],
        "home_care": "Eat smaller meals, avoid lying down immediately after eating, avoid spicy and greasy food, elevate head during sleep.",
        "when_to_see_doctor": "See a physician if you experience difficulty swallowing, unexplained weight loss, persistent vomiting, or black stools."
    },
    {
        "keywords": ["allergy", "itching", "hives", "rash", "watery eyes", "allergic"],
        "condition": "Mild Allergic Reaction or Rhinitis",
        "general_medicines": ["Cetirizine (10 mg)", "Loratadine (10 mg)", "Calamine lotion for skin irritation"],
        "home_care": "Avoid known allergens, keep skin cool and moisturized, avoid scratching affected areas.",
        "when_to_see_doctor": "CALL EMERGENCY SERVICES IMMEDIATELY if experiencing swelling of lips/tongue/throat, difficulty breathing, or anaphylaxis."
    },
    {
        "keywords": ["nausea", "vomiting", "upset stomach", "motion sickness"],
        "condition": "Mild Nausea or Stomach Upset",
        "general_medicines": ["Oral Rehydration Salts (ORS)", "Ginger lozenges", "Domperidone / Ondansetron (prescription only)"],
        "home_care": "Sip clear fluids or electrolyte solutions slowly. Follow the BRAT diet (bananas, rice, applesauce, toast).",
        "when_to_see_doctor": "Consult a doctor if unable to keep fluids down for 24 hours, signs of dehydration, or severe abdominal pain."
    }
]

DISCLAIMER_TEXT = "This information is for general guidance only. Consult a qualified doctor or pharmacist before taking any medicine."


def find_medicine_in_text(raw_text):
    """
    Search extracted OCR text for genuine medicine names and extract dosage info.
    Returns detected dict or None.
    """
    if not raw_text or len(raw_text.strip()) < 3:
        return None

    cleaned_text = raw_text.lower()
    
    # Search for match in database
    matched_entry = None
    for med_key, med_data in MEDICINE_DATABASE.items():
        # Check word boundary regex to avoid partial substring mismatches
        pattern = r"\b" + re.escape(med_key) + r"\b"
        if re.search(pattern, cleaned_text):
            matched_entry = med_data
            break

    if not matched_entry:
        return None

    # Try to extract explicit dosage in the text (e.g., "500 mg", "20mg", "1000 IU")
    dosage_pattern = r"(\d{1,4})\s*(mg|ml|mcg|iu|g)\b"
    dose_match = re.search(dosage_pattern, cleaned_text)
    
    dosage_amount = matched_entry["default_dosage"]
    dosage_unit = matched_entry["unit"]
    
    if dose_match:
        dosage_amount = dose_match.group(1)
        dosage_unit = dose_match.group(2)

    return {
        "status": "success",
        "medicine_found": True,
        "name": matched_entry["name"],
        "generic_name": matched_entry["generic_name"],
        "category": matched_entry["category"],
        "dosage_amount": dosage_amount,
        "dosage_unit": dosage_unit,
        "dosage_limit": matched_entry["limit"],
        "frequency": matched_entry["frequency"],
        "doses_per_day": matched_entry["doses_per_day"],
        "suggested_usage": matched_entry["suggested_usage"],
        "warnings": matched_entry["warnings"],
        "notes": f"Suggested: {matched_entry['suggested_usage']}"
    }


def get_medicine_suggestions(symptoms_text):
    """
    Match user symptoms against clinical guidance database.
    """
    if not symptoms_text or len(symptoms_text.strip()) < 2:
        return {
            "status": "error",
            "message": "Please enter your symptoms to receive general information.",
            "disclaimer": DISCLAIMER_TEXT
        }

    tokens = [t.lower().strip() for t in re.split(r"[,;.\s]+", symptoms_text) if len(t) > 2]
    matched = []

    for item in SYMPTOM_SUGGESTIONS:
        match_count = sum(1 for kw in item["keywords"] if any(t in kw for t in tokens) or kw in symptoms_text.lower())
        if match_count > 0:
            matched.append((match_count, item))

    matched.sort(key=lambda x: x[0], reverse=True)

    if not matched:
        return {
            "status": "success",
            "condition": "General Health Query",
            "general_medicines": ["Hydration & Rest", "Consult a physician for targeted therapy"],
            "home_care": "Maintain adequate hydration, eat balanced nutritious meals, and monitor your symptoms closely.",
            "when_to_see_doctor": "Consult a licensed healthcare professional if symptoms persist beyond 48 hours or worsen.",
            "disclaimer": DISCLAIMER_TEXT
        }

    top_item = matched[0][1]
    return {
        "status": "success",
        "condition": top_item["condition"],
        "general_medicines": top_item["general_medicines"],
        "home_care": top_item["home_care"],
        "when_to_see_doctor": top_item["when_to_see_doctor"],
        "disclaimer": DISCLAIMER_TEXT
    }
