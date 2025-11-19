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

## 🛡️ Logs & supervision

- Les scripts enregistrent leur activité dans `logs/`.
- Les erreurs/états critiques sont visibles dans les logs et via les KPI “Stations sous le seuil”.