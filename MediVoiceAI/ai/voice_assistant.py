"""
MediVoice AI - Voice Assistant Engine
Processes natural language voice/text commands and returns conversational answers,
action triggers, and speech synthesis instructions.
"""

from datetime import datetime
import re

def process_voice_command(user, command_text, medicines, today_logs):
    """
    Process incoming voice/text prompt from the user against their personal schedule.
    """
    cmd = command_text.strip().lower() if command_text else ""
    now_time = datetime.now()
    now_str = now_time.strftime("%I:%M %p")
    today_date = now_time.strftime("%Y-%m-%d")

    # 1. "Add a medicine."
    if any(k in cmd for k in ["add a medicine", "add medicine", "new medicine", "create medicine", "enter medicine"]):
        return {
            "text": "Opening the medicine creation form for you. You can enter the name, dosage, and reminder times.",
            "spoken": "Opening the add medicine screen.",
            "action": "navigate",
            "url": "/medicines/add"
        }

    # 2. "What medicines do I have today?"
    if any(k in cmd for k in ["medicines do i have today", "medicines today", "what do i take today", "today's medicines", "today schedule"]):
        if not medicines:
            return {
                "text": "You do not have any medicines registered yet. Would you like me to open the add medicine form?",
                "spoken": "You have no medicines scheduled for today.",
                "action": "none"
            }
        med_names = [f"{m.name} ({m.dosage_amount} {m.dosage_unit} at {m.reminder_time})" for m in medicines if m.is_active]
        if not med_names:
            return {
                "text": "All your registered medicines are currently inactive.",
                "spoken": "You have no active medicines for today.",
                "action": "none"
            }
        response_text = f"You have {len(med_names)} active medicine(s) today: " + "; ".join(med_names) + "."
        spoken_text = f"Today you have: " + ", ".join([f"{m.name}, {m.dosage_amount} {m.dosage_unit}" for m in medicines if m.is_active]) + "."
        return {
            "text": response_text,
            "spoken": spoken_text,
            "action": "none"
        }

    # 3. "When is my next medicine reminder?"
    if any(k in cmd for k in ["next medicine reminder", "next reminder", "when is my next", "next dose"]):
        active_meds = [m for m in medicines if m.is_active]
        if not active_meds:
            return {
                "text": "No active medicines found to remind you about.",
                "spoken": "You don't have any active medicine reminders scheduled.",
                "action": "none"
            }
        # Find next reminder time
        first_med = active_meds[0]
        return {
            "text": f"Your next scheduled reminder is for {first_med.name} ({first_med.dosage_amount} {first_med.dosage_unit}) at {first_med.reminder_time}.",
            "spoken": f"Your next reminder is {first_med.name}, {first_med.dosage_amount} {first_med.dosage_unit} at {first_med.reminder_time}.",
            "action": "none"
        }

    # 4. "What is my dosage?" or "What is the dosage of this medicine?"
    if any(k in cmd for k in ["what is my dosage", "what is the dosage", "dosage of this medicine", "how much should i take"]):
        # Check if a specific medicine name is mentioned
        matched_med = None
        for m in medicines:
            if m.name.lower() in cmd:
                matched_med = m
                break
        
        if matched_med:
            return {
                "text": f"The dosage for {matched_med.name} is {matched_med.dosage_amount} {matched_med.dosage_unit}, {matched_med.frequency}. Daily limit: {matched_med.dosage_limit}.",
                "spoken": f"The dosage for {matched_med.name} is {matched_med.dosage_amount} {matched_med.dosage_unit}.",
                "action": "none"
            }
        elif medicines:
            summary = ", ".join([f"{m.name}: {m.dosage_amount} {m.dosage_unit}" for m in medicines])
            return {
                "text": f"Your registered dosages are: {summary}.",
                "spoken": f"Your prescribed dosages are: {summary}.",
                "action": "none"
            }
        else:
            return {
                "text": "No medicines currently on record. Add one to track dosage.",
                "spoken": "No medicines found in your account.",
                "action": "none"
            }

    # 5. "Show my medicine history."
    if any(k in cmd for k in ["medicine history", "show my history", "dosage history", "past medicines", "log"]):
        return {
            "text": "Navigating to your complete medicine and dosage history.",
            "spoken": "Here is your medicine history.",
            "action": "navigate",
            "url": "/history"
        }

    # 6. "What medicines are scheduled now?"
    if any(k in cmd for k in ["scheduled now", "medicines right now", "take right now", "due now"]):
        pending_logs = [log for log in today_logs if log.status == "pending"]
        if pending_logs:
            items = ", ".join([f"{l.medicine.name if l.medicine else 'Medicine'} at {l.scheduled_time}" for l in pending_logs])
            return {
                "text": f"You have pending doses scheduled around now: {items}.",
                "spoken": f"You have pending medicine doses: {items}.",
                "action": "none"
            }
        else:
            return {
                "text": f"No medicines are due right now. You're up to date for this hour!",
                "spoken": "No medicines are due right now. You are all caught up.",
                "action": "none"
            }

    # 7. "Remind me about my medicine."
    if any(k in cmd for k in ["remind me about my medicine", "remind me", "set reminder", "trigger reminder"]):
        active_meds = [m for m in medicines if m.is_active]
        if active_meds:
            med = active_meds[0]
            return {
                "text": f"Reminder active: It is time to take your {med.name}. Dosage: {med.dosage_amount} {med.dosage_unit}. Notes: {med.notes or 'Take as prescribed.'}",
                "spoken": f"Reminder: It is time to take {med.name}. Dosage: {med.dosage_amount} {med.dosage_unit}.",
                "action": "trigger_reminder",
                "medicine": med.to_dict()
            }
        else:
            return {
                "text": "You do not have any active medicines saved to remind you about.",
                "spoken": "Please add a medicine first to enable reminders.",
                "action": "none"
            }

    # 8. Camera / Scan command
    if any(k in cmd for k in ["scan medicine", "open camera", "scan package", "camera"]):
        return {
            "text": "Opening the camera scanner to detect medicine label and dosage.",
            "spoken": "Opening camera scanner.",
            "action": "navigate",
            "url": "/camera"
        }

    # Default fallback intelligent health assistant response
    return {
        "text": f"I heard: '{command_text}'. You can ask me 'What medicines do I have today?', 'When is my next reminder?', 'What is my dosage?', 'Add a medicine', or 'Show my medicine history'.",
        "spoken": "I am ready to help you manage your medicines and reminders. Ask about your doses or schedule.",
        "action": "none"
    }
