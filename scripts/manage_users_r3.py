"""Create a local account interactively. No password passed in arguments/logs."""
from __future__ import annotations
from getpass import getpass
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from auth_r3 import create_user, disable_user


def main():
    parser = argparse.ArgumentParser(description='Create local R&D prototype user')
    parser.add_argument('--username', required=True)
    parser.add_argument('--role', default='viewer', choices=['admin','editor','reviewer','viewer'])
    parser.add_argument('--disable', action='store_true', help='Disable account and revoke all sessions')
    args = parser.parse_args()
    if args.disable:
        disable_user(args.username)
        print(f'Đã vô hiệu hóa tài khoản {args.username} và thu hồi phiên đăng nhập')
        return
    password = getpass('Mật khẩu (ít nhất 12 ký tự): ')
    repeat = getpass('Nhập lại mật khẩu: ')
    if password != repeat:
        raise SystemExit('Mật khẩu không khớp')
    create_user(args.username, password, args.role)
    print(f'Đã tạo người dùng {args.username} với vai trò {args.role} trong cơ sở dữ liệu xác thực cục bộ')

if __name__ == '__main__': main()
