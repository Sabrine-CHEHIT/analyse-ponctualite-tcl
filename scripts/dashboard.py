import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine, text
import urllib.parse

# ==================== CONFIGURATION ====================

DB_PASSWORD = "#######"

# Encodage du mot de passe pour éviter les caractères spéciaux
password_encoded = urllib.parse.quote_plus(DB_PASSWORD)

# Connexion à PostgreSQL avec encodage explicite
engine = create_engine(
    f'postgresql+psycopg2://postgres:{password_encoded}@localhost:5432/tcl_analysis',
    connect_args={'client_encoding': 'utf8'}
)

print("🔌 Connexion à PostgreSQL...")

# ==================== REQUÊTE SQL ====================
query = """
WITH analyse_ponctualite AS (
    SELECT 
        r.route_short_name AS ligne,
        EXTRACT(HOUR FROM st.arrival_time) AS heure,
        COUNT(*) AS nb_passages,
        ROUND(100.0 * SUM(CASE WHEN st.retard_secondes < 300 THEN 1 ELSE 0 END) / COUNT(*), 2) AS taux_ponctualite_pct,
        ROUND(AVG(st.retard_secondes)::numeric, 1) AS retard_moyen_sec
    FROM stop_times st
    JOIN trips t ON st.trip_id = t.trip_id
    JOIN routes r ON t.route_id = r.route_id
    GROUP BY r.route_short_name, heure
)
SELECT * FROM analyse_ponctualite
ORDER BY ligne, heure;
"""

try:
    # Exécution de la requête
    df = pd.read_sql(query, engine)
    print("✅ Données chargées avec succès !")
    print("\n📊 Aperçu des données :")
    print(df)
except Exception as e:
    print(f"❌ Erreur lors du chargement : {e}")
    exit()

# ==================== CRÉATION DU DASHBOARD ====================
# Style professionnel
plt.style.use('seaborn-v0_8-darkgrid')
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('📊 Analyse de la ponctualité des transports lyonnais (TCL)', 
             fontsize=16, fontweight='bold')

# Couleurs
couleurs = {'A': '#3498db', 'B': '#e74c3c', 'C': '#2ecc71'}

# ===== Graphique 1 : Taux de ponctualité par ligne (barres) =====
lignes = df.groupby('ligne')['taux_ponctualite_pct'].first().index
taux_lignes = df.groupby('ligne')['taux_ponctualite_pct'].first().values
bars = axes[0, 0].bar(lignes, taux_lignes, color=['#3498db', '#e74c3c', '#2ecc71'], edgecolor='black')
axes[0, 0].set_ylim(0, 105)
axes[0, 0].set_ylabel('Taux de ponctualité (%)')
axes[0, 0].set_title('Taux de ponctualité par ligne', fontweight='bold')
axes[0, 0].axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Seuil 80%')
axes[0, 0].axhline(y=50, color='red', linestyle='--', alpha=0.5, label='Seuil 50%')
axes[0, 0].legend()
for bar, val in zip(bars, taux_lignes):
    axes[0, 0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, f'{val:.1f}%', 
                    ha='center', va='bottom', fontweight='bold')

# ===== Graphique 2 : Ponctualité par heure (lignes) =====
for ligne in ['A', 'B', 'C']:
    data = df[df['ligne'] == ligne]
    axes[0, 1].plot(data['heure'], data['taux_ponctualite_pct'], 
                    marker='o', linewidth=2, label=f'Ligne {ligne}', 
                    color=couleurs[ligne])
axes[0, 1].set_xlabel('Heure de la journée')
axes[0, 1].set_ylabel('Taux de ponctualité (%)')
axes[0, 1].set_title('Évolution du taux de ponctualité par heure', fontweight='bold')
axes[0, 1].set_xticks([8, 12, 18])
axes[0, 1].set_ylim(0, 105)
axes[0, 1].axhline(y=80, color='green', linestyle='--', alpha=0.5)
axes[0, 1].axhline(y=50, color='red', linestyle='--', alpha=0.5)
axes[0, 1].legend()
axes[0, 1].grid(True, alpha=0.3)

# ===== Graphique 3 : Heatmap ligne × heure =====
pivot = df.pivot(index='ligne', columns='heure', values='taux_ponctualite_pct')
im = axes[1, 0].imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
axes[1, 0].set_xticks(range(len(pivot.columns)))
axes[1, 0].set_xticklabels([f'{int(h)}h' for h in pivot.columns])
axes[1, 0].set_yticks(range(len(pivot.index)))
axes[1, 0].set_yticklabels([f'Ligne {l}' for l in pivot.index])
axes[1, 0].set_xlabel('Heure')
axes[1, 0].set_title('Carte de chaleur : Ponctualité par ligne et par heure', fontweight='bold')
for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        axes[1, 0].text(j, i, f'{pivot.iloc[i, j]:.0f}%',
                        ha="center", va="center", color="black", fontweight='bold', fontsize=10)
plt.colorbar(im, ax=axes[1, 0], label='Taux de ponctualité (%)')

# ===== Graphique 4 : Retard moyen par ligne =====
retards = df.groupby('ligne')['retard_moyen_sec'].first()
bars2 = axes[1, 1].bar(retards.index, retards.values, color=['#3498db', '#e74c3c', '#2ecc71'], edgecolor='black')
axes[1, 1].set_ylabel('Retard moyen (secondes)')
axes[1, 1].set_title('Retard moyen par ligne', fontweight='bold')
axes[1, 1].axhline(y=300, color='red', linestyle='--', alpha=0.7, label='Seuil 5 min (300s)')
axes[1, 1].legend()
for bar, val in zip(bars2, retards.values):
    axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, f'{val:.1f}s', 
                    ha='center', va='bottom', fontweight='bold')

plt.tight_layout()
plt.savefig('dashboard_ponctualite.png', dpi=150, bbox_inches='tight')
print("\n✅ Dashboard sauvegardé : dashboard_ponctualite.png")
plt.show()

# ==================== EXPORT DES DONNÉES POUR GITHUB ====================
df.to_csv('analyse_complete.csv', index=False, encoding='utf-8-sig')
print("✅ Données exportées : analyse_complete.csv")

# ==================== STATISTIQUES CLÉS ====================
print("\n" + "="*50)
print("📈 STATISTIQUES CLÉS")
print("="*50)

# Ligne la moins ponctuelle
pire_ligne = df.groupby('ligne')['taux_ponctualite_pct'].min()
pire = pire_ligne.idxmin()
print(f"🔴 Ligne la moins ponctuelle : Ligne {pire} ({pire_ligne[pire]:.1f}% à l'heure)")

# Heure la plus critique
pire_heure = df.groupby('heure')['taux_ponctualite_pct'].min()
heure_critique = pire_heure.idxmin()
print(f"⏰ Heure la plus critique : {heure_critique}h ({pire_heure[heure_critique]:.1f}% de ponctualité)")

# Meilleure combinaison
meilleur = df.loc[df['taux_ponctualite_pct'].idxmax()]
print(f"🏆 Meilleure combinaison : Ligne {meilleur['ligne']} à {meilleur['heure']:.0f}h ({meilleur['taux_ponctualite_pct']:.1f}%)")

# Pire combinaison
pire = df.loc[df['taux_ponctualite_pct'].idxmin()]
print(f"💀 Pire combinaison : Ligne {pire['ligne']} à {pire['heure']:.0f}h ({pire['taux_ponctualite_pct']:.1f}%)")

# Écart entre meilleure et pire ligne
ecart = taux_lignes.max() - taux_lignes.min()
print(f"\n📊 Écart de performance : {ecart:.1f} points entre la meilleure et la pire ligne")
