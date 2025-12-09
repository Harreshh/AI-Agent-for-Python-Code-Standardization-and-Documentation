import json
import os  # ENCORE UN IMPORT (Doublon)
import re  # sert a rien celui la
import sys  # import inutile et mal formate
import time  # Sleepy time
from datetime import datetime


def complex_logic(a, b):
    # DEBUT DE LA FONCTION
    # Indentation horrible (1 espace ici)
    x = 10  # variable locale inutile (Protegee par commentaire)
    y = 20  # autre variable inutile (Protegee par commentaire)

    # Indentation bizarre (3 espaces ici)
    # Une comprehension de liste mal espacee
    res = [i * 2 for i in range(a)]

    # formatting hell : espaces autour des points et parentheses
    datetime.now().isoformat()

    # Side effect variable (DOIT ETRE GARDEE car appel de fonction)
    _ = time.sleep(0.1)

    # Print avec espaces superflus
    print(f"Processing { b }")
    return res


def data_cruncher():
    # Fonction pour les data avec indentation de 3 espaces
    # Dictionnaire illisible sans espaces apres les deux-points
    data = {"key": "value", "list": [1, 2, 3], "nested": {"a": 1}}

    # Import sauvage au milieu de la fonction (inutile)

    return json.dumps(data)


if __name__ == "__main__":
    # Appel degueulasse
    val = complex_logic(5, "test")
    print(data_cruncher())
