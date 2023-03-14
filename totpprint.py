#!/usr/bin/env python3
# nuitka-project: --onefile
# nuitka-project: --enable-plugin=tk-inter
# nuitka-project: --include-package-data=escpos
#### nuitka#project: --disable-console

import argparse

import PySimpleGUI as sg

from escpos.printer import Usb
from escpos.escpos import EscposIO
from qrcode import ERROR_CORRECT_H

parser = argparse.ArgumentParser(description='Print TOTP QR code via thermal printer')
parser.add_argument('-t', '--token', help='The TOTP key to print', type=str, default=None)
parser.add_argument('-d', '--desc', help='A short name or sentence describing what the key is', type=str, default=None)
parser.add_argument('--vid', default='0x6868', type=str, help='The USB vendor ID of the printer.')
parser.add_argument('--pid', default='0x0200', type=str, help='The USB product ID of the printer.')
parser.add_argument('--media_width', default=48, type=int, help='printer media width (print width) in mm')
parser.add_argument('--dots', default=384, type=int, help='How many dots per line the printer has')
parser.add_argument('--nogui', default=False)

args = parser.parse_args()

if args.nogui:
    if args.token is None:
        args.token = input("Enter token: ")

    if args.desc is None:
        args.desc = input("Enter description: ")

def init(vid: str, pid: str, mm: int, dots: int):

    print(f'Init with: VID:{vid} PID:{pid} width{mm}mm dots/line {dots}')
    vid = int(vid, 0)
    pid = int(pid, 0)

    printer = Usb(vid, pid)
    printer.profile.media['width']['mm'] = mm
    printer.profile.media['width']['pixels'] = dots

    printer.set(font='a', align='center')

    return printer


def print_totp(token: str, desc: str, printer):
    print(f'token:{token} desc:{desc}')
    printer.printer.textln(desc)
    qrstr = f'otpauth://totp/backup@example.com?issuer={desc.replace(" ", "_")}-Backup&secret={token}'
    printer.printer.qr(qrstr, ec=ERROR_CORRECT_H, size=4, center=True)
    printer.printer.block_text(f'{token}', font='a', columns=16)


if __name__ == '__main__':
    if args.nogui:
        with EscposIO(init(args.vid, args.pid, args.media_width, args.dots)) as prn:
            print_totp(args.token, args.desc, prn)
    else:
        sg.theme('DarkAmber')

        col1 = [
            [sg.Text('VID')],
            [sg.Text('Print width')],
            [sg.Text('TOTP token:')],
            [sg.Text('Description:')]
        ]

        col2 = [
            [sg.Input(default_text=args.vid)],
            [sg.Input(default_text=args.media_width)],
            [sg.Input()],
            [sg.Input(default_text='Unknown')]
        ]

        col3 = [
            [sg.Text('')],
            [sg.Text('mm')],
            [sg.Text('')],
            [sg.Text('')]
        ]

        col4 = [
            [sg.Text('PID')],
            [sg.Text('pixels/line')],
            [sg.Text('')],
            [sg.Text('')]
        ]

        col5 = [
            [sg.Input(default_text=args.pid)],
            [sg.Input(default_text=args.dots)],
            [sg.Text('')],
            [sg.Text('')]
        ]


        layout = [
            [sg.Column(col1), sg.Column(col2), sg.Column(col3, pad=((0,30),(0,0))), sg.Column(col4), sg.Column(col5)],
            [sg.Button('Print'), sg.Button('Cut')]
        ]

        window = sg.Window('TOTP thermal printer', layout)

        last_values = []
        while True:
            event, values = window.read()
            
            if event == 'Print':
                last_values = values
                with EscposIO(init(values[0], values[4], values[1], values[5]), autocut=False) as prn:
                    prn.printer.textln('__________')
                    print_totp(values[2], values[3], prn)
                    prn.printer.ln(2)

            elif event == sg.WIN_CLOSED:
                if len(last_values) > 0:
                    with EscposIO(init(last_values[0], last_values[4], last_values[1], last_values[5]), autocut=False) as prn:
                        prn.printer.cut()
                break
            
            elif event == 'Cut':
                with EscposIO(init(values[0], values[4], values[1], values[5]), autocut=False) as prn:
                    prn.printer.cut()
                    last_values = []

                