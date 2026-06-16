# -*- coding: utf-8 -*-
"""
UMOE OS 8.0 - Parser PBIX: extrai nomes de tabelas do Report/Layout e DAX queries
PBIX = ZIP com Layout em UTF-16 LE e JSON duplamente codificado
"""
import zipfile, json, re, os, sys
from pathlib import Path

TMP_DIR = Path(r'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI\_tmp')
OUT_DIR = Path(r'C:\01 - UMOE\09 - IA\umoe-os-8\UMOE-OS-8.0\Dados-PBI')

datasets = {
    'BASE': 'BASE.pbix',
    'CST':  'CST.pbix',
    'CTRL': 'CTRL.pbix',
}

all_tables = {}

for ds, pbix_file in datasets.items():
    pbix_path = TMP_DIR / pbix_file
    if not pbix_path.exists():
        print(f'\n[{ds}] PBIX nao encontrado: {pbix_path}')
        continue

    print(f'\n{"="*55}')
    print(f'  [{ds}] {pbix_path.name}  ({pbix_path.stat().st_size//1024//1024} MB)')
    print(f'{"="*55}')

    tables = set()
    dax_queries = []

    with zipfile.ZipFile(str(pbix_path), 'r') as z:
        names = z.namelist()
        print(f'  Arquivos ({len(names)}): {", ".join(names[:8])}...')

        # ── Report/Layout: JSON com referencias Entity ─────────────
        layout_candidates = [n for n in names if 'Layout' in n and 'Static' not in n]
        for lname in layout_candidates:
            print(f'\n  Lendo: {lname}...')
            raw = z.read(lname)

            # Tentar decodificacoes
            text = None
            for enc in ['utf-16-le', 'utf-16', 'utf-8-sig', 'utf-8', 'latin-1']:
                try:
                    text = raw.decode(enc)
                    if len(text) > 100 and '{' in text:
                        print(f'  Encoding: {enc}  |  {len(text):,} chars')
                        break
                except:
                    text = None

            if not text:
                print('  Nao foi possivel decodificar Layout')
                continue

            # Padrao 1: "Entity":"NomeTabela"  (JSON normal)
            for m in re.finditer(r'"Entity"\s*:\s*"([^"]+)"', text):
                tables.add(m.group(1))

            # Padrao 2: \"Entity\":\"NomeTabela\"  (JSON dentro de string JSON escapada)
            for m in re.finditer(r'\\"Entity\\"\s*:\s*\\"([^\\"]+)\\"', text):
                tables.add(m.group(1))

            # Padrao 3: queryRef":"Tabela.Coluna"
            for m in re.finditer(r'"queryRef"\s*:\s*"([^\."\s]+)\.', text):
                tables.add(m.group(1))

            # Padrao 4: queryRef escapado
            for m in re.finditer(r'\\"queryRef\\"\s*:\s*\\"([^\\."\s]+)\\.', text):
                tables.add(m.group(1))

            # Padrao 5: 'NomeTabela'[NomeColuna] — sintaxe DAX dentro de expressoes
            for m in re.finditer(r"'([^']{2,50})'\[", text):
                v = m.group(1)
                if not v.startswith('$') and not v.startswith('Local'):
                    tables.add(v)

            print(f'  Tabelas encontradas ate agora: {len(tables)}')

            # Dump das primeiras linhas para debug
            # Mostrar trecho onde Entity aparece
            idx = text.find('Entity')
            if idx >= 0:
                print(f'  Trecho com Entity: ...{repr(text[max(0,idx-30):idx+80])}...')
            else:
                # Mostrar primeiros 200 chars para debug
                print(f'  Primeiros 200 chars: {repr(text[:200])}')

        # ── Arquivos .dax (CTRL tem DAX queries salvas) ──────────────
        dax_files = [n for n in names if n.endswith('.dax')]
        for dname in dax_files:
            raw = z.read(dname)
            for enc in ['utf-8-sig', 'utf-8', 'utf-16-le', 'latin-1']:
                try:
                    dax_text = raw.decode(enc)
                    if len(dax_text) > 5:
                        print(f'\n  DAX Query ({dname}):')
                        print(f'  {dax_text[:800]}')
                        # Extrair tabelas do DAX
                        for m in re.finditer(r"'([^']{2,50})'\[", dax_text):
                            v = m.group(1)
                            if not v.startswith('$'):
                                tables.add(v)
                        # EVALUATE 'Tabela'
                        for m in re.finditer(r"EVALUATE\s+'([^']+)'", dax_text, re.IGNORECASE):
                            tables.add(m.group(1))
                        dax_queries.append(dax_text)
                        break
                except:
                    pass

        # ── Connections: pode revelar nome do modelo ──────────────────
        if 'Connections' in names:
            try:
                conn = json.loads(z.read('Connections').decode('utf-8-sig'))
                print(f'\n  Connections: {json.dumps(conn, ensure_ascii=False)[:300]}')
            except:
                pass

        # ── DiagramLayout: pode ter nomes de tabelas ─────────────────
        if 'DiagramLayout' in names:
            try:
                raw = z.read('DiagramLayout')
                for enc in ['utf-16-le', 'utf-8']:
                    try:
                        diag = raw.decode(enc)
                        for m in re.finditer(r'"nodeIndex"\s*:\s*"([^"$][^"]*)"', diag):
                            v = m.group(1)
                            if not v.startswith('$') and not v.startswith('Local') and len(v) > 1:
                                tables.add(v)
                        if len(diag) > 10:
                            break
                    except:
                        pass
                print(f'  DiagramLayout processado. Tabelas agora: {len(tables)}')
            except Exception as e:
                print(f'  DiagramLayout erro: {e}')

    # Filtrar tabelas de sistema
    system_prefixes = ('$', 'Local', 'DateTable', 'RowNumber', 'Calendar')
    tables_clean = sorted(t for t in tables if t and not any(t.startswith(p) for p in system_prefixes))

    all_tables[ds] = tables_clean

    print(f'\n  {"-"*50}')
    print(f'  TABELAS [{ds}] ({len(tables_clean)} encontradas):')
    for t in tables_clean:
        print(f'    - {t}')

    # Salvar lista
    out = OUT_DIR / f'{ds}_TABELAS.txt'
    out.write_text('\n'.join(tables_clean), encoding='utf-8')
    print(f'\n  Lista salva: {out}')

# ── Resumo ───────────────────────────────────────────────────
print(f'\n{"="*55}')
print('  RESUMO TOTAL')
print('='*55)
for ds, tbls in all_tables.items():
    print(f'  [{ds}]: {len(tbls)} tabelas')
    for t in tbls:
        print(f'    {t}')

total = sum(len(v) for v in all_tables.values())
print(f'\n  Total: {total} tabelas mapeadas')
print('\n  Proximo passo: python pbi-dax-extrair.py')
