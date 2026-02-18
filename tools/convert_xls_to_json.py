import argparse
import json
import sys
from pathlib import Path
import subprocess
import importlib


def parse_args():
    parser = argparse.ArgumentParser(
        description="Converte arquivos .xls em JSON (um arquivo por planilha)."
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        default=None,
        help="Caminho de entrada: arquivo .xls ou diretório contendo .xls (opcional)",
    )
    parser.add_argument(
        "-o",
        "--saida",
        help="Diretório de saída para os JSON gerados (padrão: mesmo da entrada)",
    )
    parser.add_argument(
        "-r",
        "--recursivo",
        action="store_true",
        help="Buscar .xls recursivamente ao fornecer um diretório",
    )
    parser.add_argument(
        "--cabecalho",
        type=int,
        default=0,
        help="Índice da linha de cabeçalho (0-based). Padrão: 0",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentação do JSON gerado. Use 0 para compacto",
    )
    parser.add_argument(
        "--planilhas",
        nargs="*",
        help="Lista de nomes de planilhas a incluir. Se omitido, inclui todas",
    )
    parser.add_argument(
        "--mesmo_nome",
        action="store_true",
        help="Gerar um único JSON por arquivo .xls, com o mesmo nome do arquivo",
    )
    return parser.parse_args()


def sanitize_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in name).strip("_")


def discover_xls_paths(base: Path, recursive: bool) -> list[Path]:
    if base.is_file():
        return [base] if base.suffix.lower() == ".xls" else []
    if recursive:
        return sorted(p for p in base.rglob("*.xls") if p.is_file())
    return sorted(p for p in base.glob("*.xls") if p.is_file())


def ensure_out_dir(in_path: Path, out_dir_arg: str | None) -> Path:
    if out_dir_arg:
        out_dir = Path(out_dir_arg)
    else:
        out_dir = (in_path.parent if in_path.is_file() else in_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def cell_value(workbook, cell):
    import xlrd

    if cell.ctype == xlrd.XL_CELL_EMPTY:
        return None
    if cell.ctype == xlrd.XL_CELL_TEXT:
        return str(cell.value)
    if cell.ctype == xlrd.XL_CELL_NUMBER:
        val = float(cell.value)
        if val.is_integer():
            return int(val)
        return val
    if cell.ctype == xlrd.XL_CELL_DATE:
        from xlrd import xldate_as_datetime

        try:
            dt = xldate_as_datetime(cell.value, workbook.datemode)
            return dt.isoformat()
        except Exception:
            return cell.value
    if cell.ctype == xlrd.XL_CELL_BOOLEAN:
        return bool(cell.value)
    if cell.ctype == xlrd.XL_CELL_ERROR:
        return None
    return cell.value


def dedupe_keys(keys: list[str]) -> list[str]:
    seen = {}
    result = []
    for k in keys:
        base = sanitize_name(str(k)) or "col"
        count = seen.get(base, 0)
        if count == 0:
            result.append(base)
        else:
            result.append(f"{base}_{count}")
        seen[base] = count + 1
    return result


def convert_sheet(workbook, sheet, header_row: int) -> list[dict]:
    nrows = sheet.nrows
    ncols = sheet.ncols
    if nrows == 0 or ncols == 0:
        return []
    header_vals = [cell_value(workbook, sheet.cell(header_row, c)) for c in range(ncols)]
    keys = dedupe_keys([str(h) if h is not None else f"col_{i+1}" for i, h in enumerate(header_vals)])
    records = []
    for r in range(header_row + 1, nrows):
        row = {}
        for c in range(ncols):
            row[keys[c]] = cell_value(workbook, sheet.cell(r, c))
        records.append(row)
    return records


def write_json(data, out_path: Path, indent: int):
    if indent and indent > 0:
        text = json.dumps(data, ensure_ascii=False, indent=indent)
    else:
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out_path.write_text(text, encoding="utf-8")


def ensure_module(mod_name: str, pip_name: str):
    try:
        return importlib.import_module(mod_name)
    except ImportError:
        cmd = [sys.executable, "-m", "pip", "install", pip_name]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Erro ao instalar dependência: {pip_name}", file=sys.stderr)
            if r.stderr:
                print(r.stderr, file=sys.stderr)
            elif r.stdout:
                print(r.stdout, file=sys.stderr)
            sys.exit(1)
        try:
            return importlib.import_module(mod_name)
        except ImportError:
            print(f"Falha ao importar {mod_name} após instalação.", file=sys.stderr)
            sys.exit(1)


def convert_file(xls_path: Path, out_dir: Path, header_row: int, indent: int, only_sheets: list[str] | None, same_name: bool):
    ensure_module("xlrd", "xlrd")

    import xlrd
    wb = xlrd.open_workbook(xls_path.as_posix())
    base = sanitize_name(xls_path.stem)
    names = [s.name for s in wb.sheets()]
    target_names = set(only_sheets) if only_sheets else set(names)
    if same_name:
        bundle = {}
        for name in names:
            if name not in target_names:
                continue
            sh = wb.sheet_by_name(name)
            bundle[sanitize_name(name)] = convert_sheet(wb, sh, header_row)
        out_path = out_dir / f"{base}.json"
        write_json(bundle, out_path, indent)
        print(f"Gerado: {out_path}")
    else:
        for name in names:
            if name not in target_names:
                continue
            sh = wb.sheet_by_name(name)
            data = convert_sheet(wb, sh, header_row)
            out_name = f"{base}__{sanitize_name(name)}.json"
            out_path = out_dir / out_name
            write_json(data, out_path, indent)
            print(f"Gerado: {out_path}")


def main():
    args = parse_args()
    base_dir = Path(__file__).parent
    root_dir = base_dir.parent
    data_dir = root_dir / "data"
    fixed_targets = [
        base_dir / "Cardoso.XLS",
        base_dir / "Machado.XLS",
    ]
    targets: list[Path] = []
    for p in fixed_targets:
        if p.exists() and p.is_file():
            targets.append(p)
    if args.entrada is not None:
        entrada_path = Path(args.entrada)
        targets.extend(discover_xls_paths(entrada_path, args.recursivo))
    if not targets:
        targets.extend(discover_xls_paths(base_dir, False))
    if not targets:
        print("Nenhum arquivo .xls encontrado.", file=sys.stderr)
        sys.exit(2)
    seen = set()
    fixed_names = {"cardoso.xls", "machado.xls"}
    for xls in targets:
        key = xls.resolve().as_posix().lower()
        if key in seen:
            continue
        seen.add(key)
        out_dir = Path(args.saida) if args.saida else data_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        convert_file(
            xls_path=xls,
            out_dir=out_dir,
            header_row=args.cabecalho,
            indent=args.indent,
            only_sheets=args.planilhas,
            same_name=True if xls.name.lower() in fixed_names else bool(args.mesmo_nome),
        )


if __name__ == "__main__":
    main()
