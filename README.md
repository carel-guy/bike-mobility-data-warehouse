# 🚲 Observatoire VCUB – Bike Station Analytics

Une application Streamlit moderne pour surveiller en temps réel le réseau VCUB bordelais, analyser l’activité historique et identifier rapidement les stations critiques.

## ✨ Points clés

- **Données live** : ingestion du réseau VCUB via l’API CityBikes (203 stations suivies) et stockage dans SQLite (`data/bike_data.db`).
- **Dashboards immersifs** : cartes interactives, donuts, KPI instantanés et classements pour comprendre la disponibilité en un clin d’œil.
- **Analyses temporelles** : heatmaps jour/heure, tendance globale, variations nettes et évolution des stations les plus actives.
- **Scripts d’automatisation** : `scripts/track_activity.py` pour poller l’API toutes les 5 minutes, `scripts/rank_stations.py` pour calculer les classements hors ligne.

## 🧱 Structure

```
├── dashboard.py           # Application Streamlit principale
├── streamlit_helpers.py   # Fonctions de data prep & charts
├── scripts/               # Collecte & batch analytics
├── utils/                 # Accès DB & logging
├── data/bike_data.db      # Base SQLite (générée automatiquement)
└── styles.css             # Thème custom Streamlit
```

## 🚀 Démarrage

1. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```
2. **Lancer les scripts de collecte**
   ```bash
   python scripts/fetch_stations.py      # snapshot ponctuel
   python scripts/track_activity.py      # tracking continu
   ```
3. **Ouvrir le dashboard**
   ```bash
   streamlit run dashboard.py
   ```

## 📊 Fonctionnalités du dashboard

- **KPI & donuts** : total de vélos, bornes, disponibilité globale, stations critiques.
- **Carte interactive** : cercles dimensionnés par capacité, couleur selon disponibilité.
- **Stations en direct** : tables paginées (sous seuil / plus disponibles / toutes les stations avec pagination).
- **Visualisations avancées** :
  - santé instantanée des stations (scatter),
  - dynamique des stations (turn-over vs stocks),
  - tendances historiques (ligne + heatmap).
- **Classements** : top stations par mouvements, tableau des mouvements moyens.

## 🧠 Défi avancé : détecter les vélos potentiellement défectueux

> Objectif : tirer parti des séries temporelles pour repérer les vélos qui resteraient bloqués dans des stations pourtant actives, signe possible d’une panne ou d’un abandon. Cette approche illustre comment l’ingénierie de données alimente l’intelligence opérationnelle.

1. **Hypothèse** : une station active voit régulièrement des retraits et retours. Si le stock ne baisse jamais pendant une période prolongée (ex. > 15 min) alors que l’activité alentour est forte, certains vélos sont peut-être inutilisables.
2. **Statistiques glissantes** : calculer pour chaque station un indicateur de `turnover` (variation absolue des vélos) sur une fenêtre mobile.
3. **Stations très actives** : filtrer celles dont le turnover moyen dépasse un seuil (# mouvements/minute).
4. **Détection** : repérer dans ces stations les intervalles où `free_bikes` reste quasi constant (écart < 1) malgré le statut « actif ».
5. **Alertes & visualisation** : envoyer une notification (logs, Slack, etc.) et afficher les anomalies (icône spéciale sur la carte, badge dans le tableau).

Ce pattern s’applique à tout cas d’usage de détection d’anomalies opérationnelles : on quantifie le comportement normal, puis on scrute les écarts persistants qui méritent l’œil humain.

## 🛡️ Logs & supervision

- Les scripts enregistrent leur activité dans `logs/`.
- Les erreurs/états critiques sont visibles dans les logs et via les KPI “Stations sous le seuil”.
- **Historique enrichi** : la section « Recherche de station » peut indiquer le temps passé sous/sur le seuil et afficher un badge si la station figure parmi les anomalies « vélo bloqué », pour relier la vue détaillée à l’analyse globale.
