# import sqlite3
# c = sqlite3.connect('evcs_database.db'); cur = c.cursor()
# print('pois total:', cur.execute('SELECT COUNT(*) FROM pois').fetchone()[0])
# print('eletropostos total:', cur.execute('SELECT COUNT(*) FROM eletropostos').fetchone()[0])
# print('--- malha_cache por tipo ---')
# for r in cur.execute('SELECT tipo_busca, COUNT(*) FROM malha_cache GROUP BY tipo_busca'): print('  ', r)
# print('bbox de todos os pois:', cur.execute('SELECT ROUND(MIN(lat),2),ROUND(MAX(lat),2),ROUND(MIN(lng),2),ROUND(MAX(lng),2) FROM pois').fetchone())
# q = 'SELECT COUNT(*) FROM pois WHERE lat BETWEEN -23.8 AND -22.4 AND lng BETWEEN -46.8 AND -44.6'
# print('pois na bbox do corredor Dutra:', cur.execute(q).fetchone()[0])
# c.close()


import sqlite3
c = sqlite3.connect('evcs_database.db')
c.execute('DELETE FROM malha_cache'); c.commit(); c.close()
print('malha_cache limpa.')