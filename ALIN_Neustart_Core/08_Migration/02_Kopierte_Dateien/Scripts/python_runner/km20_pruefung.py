import sys, json
from pathlib import Path
ROOT = Path(r'I:/KI_Legal_Project')
B = ROOT / 'Agentensteuerung/20_Quellen_Fundstellen_Konsolidierung'
def t(bez, bed, tests, fl):
    if bed: tests.append(1); print('  [OK] ' + bez)
    else: fl.append(bez); print('  [FEHLER] ' + bez)
tests=[]; fl=[]
for i,(p,n) in enumerate([('02_Status/KM20_STATUS.json','Status'),('03_Berichte/KM20_BERICHT.txt','Bericht'),('05_Fehler/KM20_FEHLER.txt','Fehler'),('07_Manifest/KM20_MASTER_INDEX.json','Master'),('07_Manifest/KM20_MASTER_INDEX.csv','MasterCSV'),('08_Konsolidierung/KM20_KONSOLIDIERUNG.json','Kons'),('08_Konsolidierung/KM20_KONSOLIDIERUNG.csv','KonsCSV'),('09_Unsicherheiten/KM20_UNSICHERHEITEN.json','Uns'),('10_Rueckbindung/KM20_RUECKBINDUNG.json','Rb'),('08_Konsolidierung/KM20_TESTDATEN.json','Test'),('03_Berichte/KM20_PRODUKTIV_BERICHT.txt','ProdBer')]):
    t(f'{i+1:02d} {n}', (B/p).exists(), tests, fl)
master=json.loads((B/'07_Manifest/KM20_MASTER_INDEX.json').read_text(encoding='utf-8-sig'))
t('12 Master-Seiten=24', master.get('anzahl_seiten')==24, tests, fl)
t('13 Master-Originale=3', master.get('anzahl_originale')==3, tests, fl)
t('14 Master-Schluessel=24', len(master.get('schluessel',[]))==24, tests, fl)
kons=json.loads((B/'08_Konsolidierung/KM20_KONSOLIDIERUNG.json').read_text(encoding='utf-8-sig'))
e=kons['eintraege']
t('15 Kons-Eintraege=24', len(e)==24, tests, fl)
oids=set(z['original_id'] for z in e)
t('16 Original-IDs=3', len(oids)==3, tests, fl)
t('17 Kein-Testdummy', 'ORG-TEST-KM14' not in oids, tests, fl)
fs=sum(z['fundstellen_km14_anzahl'] for z in e)
ue=sum(z['uebersetzungseinheiten_km15_anzahl'] for z in e)
t('18 FS==UE', fs==ue, tests, fl)
t('19 FS=4560', fs==4560, tests, fl)
t('20 RB_depth>=3', max((z['rueckbindung_anzahl'] for z in e),default=0)>=3, tests, fl)
test=json.loads((B/'08_Konsolidierung/KM20_TESTDATEN.json').read_text(encoding='utf-8-sig'))
t('21 Testdaten=1', len(test.get('eintraege',[]))==1, tests, fl)
t('22 Testdaten-0-FS', sum(z['fundstellen_km14_anzahl'] for z in test['eintraege'])==0, tests, fl)
status=json.loads((B/'02_Status/KM20_STATUS.json').read_text(encoding='utf-8-sig'))
t('23 Status-testdaten-out', status.get('testdaten_ausgeschlossen',0)>=1, tests, fl)
print(f'\nKM20 PRUEFUNG: {len(tests)}/23 BESTANDEN')
if fl: [print(f'  FEHLER: {f}') for f in fl]
sys.exit(0 if len(tests)==23 else 1)
