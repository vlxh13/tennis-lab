#!/usr/bin/env python3
"""
Récupère les actualités du jour depuis plusieurs flux RSS français.
Génère un fichier markdown avec les gros titres organisés par catégorie.
"""

import feedparser
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import time

# Sources RSS françaises (gratuites) - classées par catégorie
SOURCES = {
    # FRANCE / POLITIQUE
    "France Info - France": {
        "url": "https://www.francetvinfo.fr/france.rss",
        "category": "FRANCE"
    },
    "Le Monde - Politique": {
        "url": "https://www.lemonde.fr/politique/rss_full.xml",
        "category": "FRANCE"
    },
    "Le Figaro - Politique": {
        "url": "https://www.lefigaro.fr/rss/figaro_politique.xml",
        "category": "FRANCE"
    },
    # INTERNATIONAL
    "France Info - Monde": {
        "url": "https://www.francetvinfo.fr/monde.rss",
        "category": "INTERNATIONAL"
    },
    "Le Monde - International": {
        "url": "https://www.lemonde.fr/international/rss_full.xml",
        "category": "INTERNATIONAL"
    },
    "France 24": {
        "url": "https://www.france24.com/fr/rss",
        "category": "INTERNATIONAL"
    },
    # ÉCONOMIE
    "France Info - Eco": {
        "url": "https://www.francetvinfo.fr/economie.rss",
        "category": "ÉCONOMIE"
    },
    "Le Monde - Eco": {
        "url": "https://www.lemonde.fr/economie/rss_full.xml",
        "category": "ÉCONOMIE"
    },
    "Le Figaro - Eco": {
        "url": "https://www.lefigaro.fr/rss/figaro_economie.xml",
        "category": "ÉCONOMIE"
    },
    # SOCIÉTÉ
    "France Info - Société": {
        "url": "https://www.francetvinfo.fr/societe.rss",
        "category": "SOCIÉTÉ"
    },
    "Le Monde - Société": {
        "url": "https://www.lemonde.fr/societe/rss_full.xml",
        "category": "SOCIÉTÉ"
    },
    # SPORT
    "France Info - Sport": {
        "url": "https://www.francetvinfo.fr/sports.rss",
        "category": "SPORT"
    },
    "Le Monde - Sport": {
        "url": "https://www.lemonde.fr/sport/rss_full.xml",
        "category": "SPORT"
    },
    # CULTURE / TECH
    "France Info - Culture": {
        "url": "https://www.francetvinfo.fr/culture.rss",
        "category": "CULTURE"
    },
    "Le Monde - Tech": {
        "url": "https://www.lemonde.fr/pixels/rss_full.xml",
        "category": "TECH"
    },
}

def fetch_feed(name, config, max_items=8, max_age_hours=24):
    """Récupère un flux RSS et retourne les articles des dernières 24h."""
    try:
        feed = feedparser.parse(config["url"])
        articles = []
        now = datetime.now()
        cutoff = now - timedelta(hours=max_age_hours)

        for entry in feed.entries:
            if len(articles) >= max_items:
                break

            # Vérifier la date de publication
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])

            # Si pas de date ou article trop vieux, skip
            if not pub_date or pub_date < cutoff:
                continue

            title = entry.get("title", "Sans titre")
            # Nettoyer la description
            desc = entry.get("summary", entry.get("description", ""))
            # Enlever les tags HTML basiques
            desc = desc.replace("<p>", "").replace("</p>", "").replace("<br>", " ").replace("<br/>", " ")
            # Tronquer si trop long
            if len(desc) > 200:
                desc = desc[:200].rsplit(" ", 1)[0] + "..."

            articles.append({
                "title": title,
                "description": desc,
                "source": name,
                "category": config["category"],
                "link": entry.get("link", ""),
                "date": pub_date
            })
        return articles
    except Exception as e:
        print(f"Erreur {name}: {e}")
        return []

def generate_markdown(all_articles):
    """Génère le markdown de la revue de presse + index JSON."""
    today = datetime.now().strftime("%d %B %Y")

    # Organiser par catégorie
    by_category = {}
    for article in all_articles:
        cat = article["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(article)

    # Dédupliquer par titre similaire
    seen_titles = set()

    md = f"# REVUE DE PRESSE — {today}\n\n"
    md += f"*Générée automatiquement à {datetime.now().strftime('%H:%M')}*\n\n"

    category_order = ["FRANCE", "INTERNATIONAL", "ÉCONOMIE", "SOCIÉTÉ", "SPORT", "CULTURE", "TECH"]
    category_emoji = {
        "FRANCE": "🇫🇷",
        "INTERNATIONAL": "🌍",
        "ÉCONOMIE": "💰",
        "SOCIÉTÉ": "👥",
        "SPORT": "⚽",
        "CULTURE": "🎭",
        "TECH": "💻"
    }
    max_per_category = 5  # Max articles par catégorie

    index = 1
    toc = []  # Table des matières pour approfondir
    articles_index = {}  # Index JSON pour approfondir

    for cat in category_order:
        if cat not in by_category:
            continue

        md += f"## {cat}\n\n"
        cat_count = 0

        for article in by_category[cat]:
            if cat_count >= max_per_category:
                break

            # Skip si titre trop similaire déjà vu
            title_key = article["title"][:50].lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            emoji = category_emoji.get(cat, "📰")
            md += f"{emoji} **{article['title']}**\n"
            if article["description"]:
                md += f"   {article['description']}\n"
            md += "\n"

            toc.append(f"{index}. [{cat}] {article['title'][:50]}...")

            # Stocker dans l'index JSON
            articles_index[str(index)] = {
                "title": article["title"],
                "description": article["description"],
                "url": article["link"],
                "source": article["source"],
                "category": cat
            }

            index += 1
            cat_count += 1

    md += "---\n\n"
    md += "## POUR APPROFONDIR\n\n"
    md += "\n".join(toc)  # Tous les articles
    md += "\n\n> *Dis-moi un numéro pour creuser un sujet.*\n"

    return md, articles_index

def main():
    print("Recuperation des flux RSS...")

    all_articles = []
    for name, config in SOURCES.items():
        print(f"  - {name}...")
        articles = fetch_feed(name, config)
        all_articles.extend(articles)
        print(f"    {len(articles)} articles")

    print(f"\nTotal: {len(all_articles)} articles")

    # Générer le markdown + index JSON
    md_content, articles_index = generate_markdown(all_articles)

    # Sauvegarder le markdown
    output_dir = Path(__file__).parent
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_file = output_dir / f"actu_{date_str}.md"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # Sauvegarder l'index JSON (pour approfondir les sujets)
    json_file = output_dir / f"actu_{date_str}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(articles_index, f, ensure_ascii=False, indent=2)

    print(f"\nOK - Revue generee: {output_file}")
    print(f"OK - Index JSON: {json_file}")
    return str(output_file)

if __name__ == "__main__":
    main()
