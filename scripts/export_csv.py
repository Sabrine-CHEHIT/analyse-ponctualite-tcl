import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import psycopg2

# ==================== CONFIGURATION ====================

DB_PASSWORD = "######" 

# Méthode 1 : Avec psycopg2 direct (plus fiable)
try:
    print("🔌 Connexion directe avec psycopg2...")
    
    # Connexion avec psycopg2 (sans passer par SQLAlchemy)
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="tcl_analysis",
        user="postgres",
        password=DB_PASSWORD,
        client_encoding='UTF8'
    )
    
    # Requête SQL
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
    
    # Lecture directe
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Export CSV
    df.to_csv('analyse_complete.csv', index=False, encoding='utf-8-sig')
    
    print(f"\n✅ CSV créé avec succès !")
    print(f"📊 {len(df)} lignes exportées")
    print(f"📁 Fichier : analyse_complete.csv")
    print("\n📋 Aperçu des données :")
    print(df.to_string(index=False))
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    print("\n➡️ Vérifie que :")
    print("   1. PostgreSQL est démarré")
    print("   2. Le mot de passe est correct")
    print("   3. La base 'tcl_analysis' existe")
