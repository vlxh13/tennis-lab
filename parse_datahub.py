"""
Parser pour Tennis Metrics DataHub
Usage: Coller le texte copié du DataHub, obtenir un JSON propre
"""

import re
import json
from datetime import datetime

def parse_datahub_text(text: str, date_str: str = None) -> list:
    """
    Parse le texte copié du DataHub TM en liste de dicts.

    Args:
        text: Texte brut copié du DataHub
        date_str: Date au format "YYYY-MM-DD" (ex: "2026-01-10")

    Returns:
        Liste de matchs avec tournoi, joueurs, score, cotes
    """
    matches = []

    # Pattern pour extraire les infos
    # Format: "Tournament, Player1 / Player2 : Score. Cotes de début de match : X / Y."
    pattern = r'(\d{2}h\d{2})\s*\n.*?Result\s*\n([^,]+),\s*([^/]+)\s*/\s*([^:]+)\s*:\s*([^.]+)\.\s*Cotes de début de match\s*:\s*(\d+\.?\d*|None)\s*/\s*(\d+\.?\d*|None)'

    for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
        time_str = match.group(1)
        tournament = match.group(2).strip()
        player1 = match.group(3).strip()
        player2 = match.group(4).strip()
        score = match.group(5).strip()
        odds1 = match.group(6).strip()
        odds2 = match.group(7).strip()

        # Convertir les cotes en float si possible
        try:
            odds1 = float(odds1) if odds1 != "None" else None
        except:
            odds1 = None
        try:
            odds2 = float(odds2) if odds2 != "None" else None
        except:
            odds2 = None

        # Parser le score
        sets = score.split()

        # Déterminer le gagnant basé sur le score
        p1_sets = 0
        p2_sets = 0
        for s in sets:
            if '/' in s:
                games = s.split('/')
                if int(games[0]) > int(games[1]):
                    p1_sets += 1
                else:
                    p2_sets += 1

        winner = player1 if p1_sets > p2_sets else player2

        matches.append({
            "date": date_str,
            "time": time_str,
            "tournament": tournament,
            "player1": player1,
            "player2": player2,
            "score": score,
            "sets": sets,
            "winner": winner,
            "odds_player1": odds1,
            "odds_player2": odds2,
            "winner_odds": odds1 if winner == player1 else odds2,
            "loser_odds": odds2 if winner == player1 else odds1,
        })

    return matches


def save_to_json(matches: list, filepath: str):
    """Sauvegarde en JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(matches, f, indent=2, ensure_ascii=False)
    print(f"[OK] {len(matches)} matchs sauvegardés dans {filepath}")


# Test avec les données d'exemple
if __name__ == "__main__":
    sample_text = """
10h23
Horizontal fading line
Result
WTA Auckland, Svitolina E. / Jovic I. : 7/6 6/2. Cotes de début de match : 1.382 / 3.33.

10h03
Horizontal fading line
Result
ATP United Cup, Hurkacz H. / Fritz T. : 7/6 7/6. Cotes de début de match : 2.04 / 1.87.

07h33
Horizontal fading line
Result
Challenger Men - Singles Canberra, Blockx A. / Jodar R. : 6/4 6/4. Cotes de début de match : 2.79 / 1.49.

06h23
Horizontal fading line
Result
Challenger Men - Singles Nonthaburi, Noguchi R. / Gengel M. : 6/3 6/4. Cotes de début de match : 1.613 / 2.45.
"""

    matches = parse_datahub_text(sample_text, "2026-01-10")

    print(f"\n=== {len(matches)} matchs parsés ===\n")
    for m in matches:
        print(f"{m['tournament']}: {m['player1']} vs {m['player2']}")
        print(f"  Score: {m['score']} -> Winner: {m['winner']}")
        print(f"  Cotes: {m['odds_player1']} / {m['odds_player2']}")
        print(f"  Winner odds: {m['winner_odds']}")
        print()

    # Sauvegarder en JSON
    save_to_json(matches, "datahub_sample.json")
