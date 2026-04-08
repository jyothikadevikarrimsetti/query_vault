import asyncio, sys

async def main():
    elements = []

    import asyncpg
    pg_dbs = [
        ("apollo_analytics", "postgresql://sentinelsql:1234@10.224.0.9:5432/apollo_analytics"),
        ("apollo_financial",  "postgresql://sentinelsql:1234@10.224.0.9:5432/apollo_financial"),
    ]
    for db_name, dsn in pg_dbs:
        print(f"Crawling PostgreSQL: {db_name}...")
        conn = await asyncpg.connect(dsn)
        try:
            rows = await conn.fetch("""
                SELECT c.table_schema, c.table_name, c.column_name,
                       c.data_type, c.is_nullable, c.ordinal_position,
                       tc.constraint_type
                FROM information_schema.columns c
                JOIN information_schema.tables t
                  ON c.table_schema = t.table_schema AND c.table_name = t.table_name
                LEFT JOIN information_schema.key_column_usage kcu
                  ON c.table_schema = kcu.table_schema
                 AND c.table_name = kcu.table_name
                 AND c.column_name = kcu.column_name
                LEFT JOIN information_schema.table_constraints tc
                  ON kcu.constraint_name = tc.constraint_name
                 AND tc.constraint_type = 'PRIMARY KEY'
                WHERE t.table_type = 'BASE TABLE'
                  AND c.table_schema NOT IN ('pg_catalog','information_schema')
                ORDER BY c.table_schema, c.table_name, c.ordinal_position
            """)
            tables = {}
            for r in rows:
                key = (r['table_schema'], r['table_name'])
                tables.setdefault(key, []).append(r)
            for (schema, table), cols in tables.items():
                col_parts = []
                for c in cols:
                    pk = " (PK)" if c['constraint_type'] == 'PRIMARY KEY' else ""
                    null = "" if c['is_nullable'] == 'YES' else " NOT NULL"
                    col_parts.append(f"{c['column_name']} {c['data_type']}{pk}{null}")
                col_list = ", ".join(col_parts)
                text = (
                    f"Database {db_name}, schema {schema}, table {table}. "
                    f"Columns: {col_list}. "
                    f"Use this table to query {table.replace('_', ' ')} data."
                )
                elements.append({
                    "id": f"{db_name}.{schema}.{table}",
                    "text": text,
                    "metadata": {
                        "table_name": table,
                        "database_name": db_name,
                        "schema": schema,
                        "dialect": "postgresql",
                        "columns": [c['column_name'] for c in cols],
                    }
                })
            print(f"  -> {len(tables)} tables found")
        finally:
            await conn.close()

    try:
        import aiomysql
        mysql_ok = True
    except ImportError:
        print("WARNING: aiomysql not available, skipping MySQL")
        mysql_ok = False

    if mysql_ok:
        mysql_dbs = ["ApolloHIS", "ApolloHR"]
        for db_name in mysql_dbs:
            print(f"Crawling MySQL: {db_name}...")
            conn = await aiomysql.connect(
                host="10.224.0.10", port=3306,
                user="sentinelsql", password="1234", db=db_name
            )
            try:
                async with conn.cursor() as cur:
                    await cur.execute("""
                        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE,
                               IS_NULLABLE, ORDINAL_POSITION, COLUMN_KEY
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s
                        ORDER BY TABLE_NAME, ORDINAL_POSITION
                    """, (db_name,))
                    rows = await cur.fetchall()
                tables = {}
                for (tname, cname, dtype, nullable, pos, col_key) in rows:
                    tables.setdefault(tname, []).append((cname, dtype, nullable, col_key))
                for table, cols in tables.items():
                    col_parts = []
                    for (cname, dtype, nullable, col_key) in cols:
                        pk = " (PK)" if col_key == 'PRI' else ""
                        null = "" if nullable == 'YES' else " NOT NULL"
                        col_parts.append(f"{cname} {dtype}{pk}{null}")
                    col_list = ", ".join(col_parts)
                    text = (
                        f"Database {db_name}, table {table}. "
                        f"Columns: {col_list}. "
                        f"Use this table to query {table.replace('_', ' ')} data."
                    )
                    elements.append({
                        "id": f"{db_name}.{table}",
                        "text": text,
                        "metadata": {
                            "table_name": table,
                            "database_name": db_name,
                            "schema": db_name,
                            "dialect": "mysql",
                            "columns": [c[0] for c in cols],
                        }
                    })
                print(f"  -> {len(tables)} tables found")
            finally:
                conn.close()

    print(f"\nTotal elements: {len(elements)}")
    import httpx
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "http://localhost:8900/api/v1/schema/crawl",
            json={"elements": elements}
        )
        print("Crawl status:", resp.status_code)
        print("Crawl response:", resp.text)
        if resp.status_code != 200:
            sys.exit(1)

asyncio.run(main())
