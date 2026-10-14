"""
Shared class list for AgriSmart AI - Crop Disease Detection.

IMPORTANT: This is a placeholder list matching the *shape* described in the
problem statement (~15-20 crop-disease classes + healthy classes, present in
both PlantVillage and the PlantDoc-style field test set). The organizers
publish the exact final class list with the kickoff data -- replace this list
verbatim with that one before training, so your class indices match the
held-out test set's labels exactly.
"""

CLASS_NAMES = [
    "healthy_leaf",
    "bacteria_leaf",
]

CLASS_TO_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {i: name for i, name in enumerate(CLASS_NAMES)}

# Simple, non-diagnostic precaution text shown to the farmer alongside a
# prediction. Kept generic on purpose -- this is guidance, not agronomic
# advice, and should be reviewed/extended with a domain expert before
# real-world use.
PRECAUTIONS = {
    "bacteria_leaf": "Remove and destroy affected leaves. Avoid overhead watering, which spreads bacteria. Use disease-free seed/transplants and rotate crops. Consult a local agricultural extension officer for treatment options.",
}


def precaution_for(class_name: str) -> str:
    if class_name.endswith("Healthy"):
        return "No signs of disease detected. Continue routine monitoring."
    return PRECAUTIONS.get(
        class_name,
        "Isolate affected plants if possible and consult a local agricultural extension officer.",
    )
