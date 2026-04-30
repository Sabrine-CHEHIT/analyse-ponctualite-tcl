import pandas as pd
from sqlalchemy import create_engine, text

# ==================== CONFIGURATION ====================

DB_NAME = "tcl_analysis"
DB_USER = "postgres"
DB_PASSWORD = "######" 
DB_HOST = "localhost"
DB_PORT = "5432"

# ==================== CONNEXION ====================
print("🔌 Connexion à PostgreSQL...")
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

# Test de connexion
try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        print("✅ Connexion réussie !")
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    print("\n➡️ Vérifie que PostgreSQL est démarré et que tes identifiants sont corrects")
    exit()

# ==================== CRÉATION DES TABLES ====================
print("\n📦 Création des tables...")

with engine.connect() as conn:
    # Supprimer les tables si elles existent déjà (pour repartir de zéro)
    conn.execute(text("DROP TABLE IF EXISTS stop_times CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS trips CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS routes CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS stops CASCADE"))
    conn.execute(text("DROP TABLE IF EXISTS calendar CASCADE"))
    conn.commit()

    # Création des tables
    conn.execute(text("""
        CREATE TABLE routes (
            route_id VARCHAR(10) PRIMARY KEY,
            agency_id VARCHAR(10),
            route_short_name VARCHAR(5),
            route_long_name VARCHAR(50)
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE stops (
            stop_id VARCHAR(10) PRIMARY KEY,
            stop_name VARCHAR(100),
            stop_lat FLOAT,
            stop_lon FLOAT,
            stop_sequence INTEGER
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE calendar (
            service_id VARCHAR(5) PRIMARY KEY,
            monday INTEGER,
            tuesday INTEGER,
            wednesday INTEGER,
            thursday INTEGER,
            friday INTEGER,
            saturday INTEGER,
            sunday INTEGER,
            start_date VARCHAR(8),
            end_date VARCHAR(8)
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE trips (
            trip_id VARCHAR(20) PRIMARY KEY,
            route_id VARCHAR(10),
            service_id VARCHAR(5),
            trip_headsign VARCHAR(100),
            direction_id INTEGER,
            FOREIGN KEY (route_id) REFERENCES routes(route_id),
            FOREIGN KEY (service_id) REFERENCES calendar(service_id)
        )
    """))
    
    conn.execute(text("""
        CREATE TABLE stop_times (
            trip_id VARCHAR(20),
            arrival_time TIME,
            departure_time TIME,
            stop_id VARCHAR(10),
            stop_sequence INTEGER,
            arrival_time_reel TIME,
            departure_time_reel TIME,
            retard_secondes FLOAT,
            PRIMARY KEY (trip_id, stop_sequence),
            FOREIGN KEY (trip_id) REFERENCES trips(trip_id),
            FOREIGN KEY (stop_id) REFERENCES stops(stop_id)
        )
    """))
    conn.commit()

print("✅ Tables créées")

# ==================== IMPORT DES DONNÉES ====================
print("\n📤 Import des fichiers CSV...")

# 1. routes.csv
df_routes = pd.read_csv("routes.csv")
df_routes.to_sql("routes", engine, if_exists="append", index=False)
print(f"   ✅ routes : {len(df_routes)} lignes")

# 2. stops.csv
df_stops = pd.read_csv("stops.csv")
df_stops.to_sql("stops", engine, if_exists="append", index=False)
print(f"   ✅ stops : {len(df_stops)} lignes")

# 3. calendar.csv
df_calendar = pd.read_csv("calendar.csv")
df_calendar.to_sql("calendar", engine, if_exists="append", index=False)
print(f"   ✅ calendar : {len(df_calendar)} lignes")

# 4. trips.csv
df_trips = pd.read_csv("trips.csv")
df_trips.to_sql("trips", engine, if_exists="append", index=False)
print(f"   ✅ trips : {len(df_trips)} lignes")

# 5. stop_times.csv (le plus gros)
df_stop_times = pd.read_csv("stop_times.csv")
df_stop_times.to_sql("stop_times", engine, if_exists="append", index=False)
print(f"   ✅ stop_times : {len(df_stop_times)} lignes")

# ==================== VÉRIFICATION FINALE ====================
print("\n🔍 Vérification des imports...")

with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT 'routes' AS table_name, COUNT(*) FROM routes
        UNION ALL
        SELECT 'stops', COUNT(*) FROM stops
        UNION ALL
        SELECT 'calendar', COUNT(*) FROM calendar
        UNION ALL
        SELECT 'trips', COUNT(*) FROM trips
        UNION ALL
        SELECT 'stop_times', COUNT(*) FROM stop_times
    """))
    
    print("\n📊 Comptage final :")
    for row in result:
        print(f"   {row[0]}: {row[1]} lignes")

print("\n🎉 IMPORT TERMINÉ AVEC SUCCÈS !")
print("👉 Tu peux maintenant exécuter tes requêtes SQL dans pgAdmin.")
