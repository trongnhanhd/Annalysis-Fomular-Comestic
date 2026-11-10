"""Command-line analysis: python cli.py examples/serum_eu.json --output report.json"""
import argparse
import json
from pathlib import Path
from engine import analyze


def main():
    parser = argparse.ArgumentParser(description='Suy luận khoảng nồng độ nguyên liệu INCI (% w/w)')
    parser.add_argument('input', type=Path, help='Đường dẫn file JSON đầu vào')
    parser.add_argument('--output', type=Path, help='Tệp JSON kết quả (nếu không chỉ in ra stdout)')
    args = parser.parse_args()
    result = analyze(json.loads(args.input.read_text(encoding='utf-8')))
    content = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
        print(f'Đã ghi báo cáo: {args.output}')
    else:
        print(content)
    raise SystemExit(0 if result['status']=='feasible' else 2)


if __name__ == '__main__':
    main()
