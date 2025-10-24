import psycopg2

conn = psycopg2.connect(
    host='192.168.178.94',
    port=5432,
    user='postgres',
    password='postgres',
    database='postgres'
)
cur = conn.cursor()

# Get tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
tables = [row[0] for row in cur.fetchall()]
print(f"Tables ({len(tables)}):", tables)

# Get columns for documents table (if exists)
if 'documents' in tables:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'documents' ORDER BY ordinal_position")
    columns = [row[0] for row in cur.fetchall()]
    print(f"\nDocuments columns:", columns)
    
    # Get sample data
    cur.execute("SELECT * FROM documents LIMIT 1")
    sample = cur.fetchone()
    if sample:
        print(f"\nSample data: {dict(zip(columns, sample))}")
else:
    print("\n❌ 'documents' table not found!")
    print("Looking for similar tables...")
    for table in tables:
        if 'doc' in table.lower():
            print(f"  - {table}")

cur.close()
conn.close()
