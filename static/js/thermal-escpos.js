/**
 * Direct ESC/POS Thermal Printer Client (58mm / 32-column)
 * Supports:
 *  1. Web Serial API (Bluetooth Classic SPP COM Port on Windows / USB Serial)
 *  2. Web Bluetooth API (BLE Thermal Printers)
 * Command bytes follow the 58MM Printer Programmer Manual (Command.java).
 */
(function (window) {
    'use strict';

    var ESC = 0x1B;
    var GS = 0x1D;
    var LF = 0x0A;
    var DEFAULT_LINE_WIDTH = 48; // 80mm = 48 chars, 58mm = 32 chars

    var BLE_SERVICE_UUIDS = [
        '000018f0-0000-1000-8000-00805f9b34fb',
        '0000ff00-0000-1000-8000-00805f9b34fb',
        '49535343-fe7d-4ae5-8fa9-9fafd205e455',
        'e7810a71-73ae-499d-8c15-faa9aef0c3f2'
    ];

    function toAsciiBytes(str) {
        var clean = String(str || '')
            .replace(/[^\x20-\x7E]/g, ' ');
        var out = [];
        for (var i = 0; i < clean.length; i++) {
            out.push(clean.charCodeAt(i) & 0x7F);
        }
        return out;
    }

    function pushBytes(buf, arr) {
        for (var i = 0; i < arr.length; i++) {
            buf.push(arr[i]);
        }
    }

    function pushLine(buf, text) {
        pushBytes(buf, toAsciiBytes(text));
        buf.push(LF);
    }

    function formatRow(left, right, width) {
        var w = width || DEFAULT_LINE_WIDTH;
        var l = String(left || '');
        var r = String(right || '');
        if (l.length + r.length + 1 <= w) {
            var spaces = w - l.length - r.length;
            return l + new Array(spaces + 1).join(' ') + r;
        }
        var maxLeft = Math.max(8, w - r.length - 1);
        return l.slice(0, maxLeft) + ' ' + r;
    }

    function buildEscPosReceipt(data, lineWidth) {
        var w = lineWidth || DEFAULT_LINE_WIDTH;
        var divider = new Array(w + 1).join('-');
        var b = [];
        // ESC @ - Initialize printer
        pushBytes(b, [ESC, 0x40]);

        // Center align header
        pushBytes(b, [ESC, 0x61, 0x01]);
        pushBytes(b, [ESC, 0x45, 0x01]); // Bold ON
        pushBytes(b, [GS, 0x21, 0x01]);  // Double height
        pushLine(b, 'JOGO TIRTO');
        pushBytes(b, [GS, 0x21, 0x00]);  // Normal size
        pushBytes(b, [ESC, 0x45, 0x00]); // Bold OFF
        pushLine(b, 'SIAP AIR BERSIH & WIFI WARGA');
        pushLine(b, 'RT 05 / RW 09');

        // Left align body
        pushBytes(b, [ESC, 0x61, 0x00]);
        pushLine(b, divider);
        pushLine(b, formatRow('No. Struk:', data.noStruk, w));
        pushLine(b, formatRow('Tanggal:', data.tanggal, w));
        pushLine(b, formatRow('Kasir:', data.kasir, w));
        pushLine(b, divider);
        pushLine(b, formatRow('Kode Member:', data.kodeMember, w));
        pushLine(b, formatRow('Pelanggan:', data.nama, w));
        pushLine(b, formatRow('Rumah:', data.rumah, w));
        pushLine(b, formatRow('No. HP:', data.noHp, w));
        pushLine(b, divider);

        var items = (data.items && data.items.length)
            ? data.items
            : [{ layanan: data.layanan, periode: data.periode, total: data.total }];
        for (var idx = 0; idx < items.length; idx++) {
            var it = items[idx];
            pushBytes(b, [ESC, 0x45, 0x01]);
            pushLine(b, it.layanan);
            pushBytes(b, [ESC, 0x45, 0x00]);
            pushLine(b, formatRow('Periode ' + it.periode, it.total, w));
        }

        pushLine(b, divider);
        pushBytes(b, [ESC, 0x45, 0x01]);
        var totalLabel = items.length > 1 ? ('TOTAL (' + items.length + ' Item)') : 'TOTAL BAYAR';
        pushLine(b, formatRow(totalLabel, data.total, w));
        pushLine(b, formatRow('Status:', data.status, w));
        pushBytes(b, [ESC, 0x45, 0x00]);
        pushLine(b, divider);

        // Footer center
        pushBytes(b, [ESC, 0x61, 0x01]);
        pushLine(b, 'Terima kasih atas pembayaran iuran Anda.');
        pushLine(b, 'Simpan struk ini sebagai bukti pembayaran sah.');

        // ESC d 4 - Feed 4 lines & partial cut (GS V B 0)
        pushBytes(b, [ESC, 0x64, 0x04]);
        pushBytes(b, [GS, 0x56, 0x42, 0x00]);
        return new Uint8Array(b);
    }

    function showStatus(msg, isError) {
        var el = document.getElementById('escposStatusAlert');
        if (!el) return;
        el.className = 'alert mb-3 ' + (isError ? 'alert-danger' : 'alert-success');
        el.textContent = msg;
        el.classList.remove('d-none');
    }

    async function printViaSerial(payloadBytes, baudRate) {
        if (!('serial' in navigator)) {
            throw new Error('Browser ini tidak mendukung Web Serial API. Gunakan Google Chrome / Microsoft Edge versi terbaru.');
        }
        var ports = await navigator.serial.getPorts();
        var port = ports && ports.length > 0 ? ports[0] : await navigator.serial.requestPort();
        var opened = false;
        try {
            await port.open({ baudRate: baudRate || 9600 });
            opened = true;
            var writer = port.writable.getWriter();
            try {
                await writer.write(payloadBytes);
            } finally {
                writer.releaseLock();
            }
        } finally {
            if (opened) {
                await port.close();
            }
        }
    }

    async function printViaBluetoothBle(payloadBytes) {
        if (!('bluetooth' in navigator)) {
            throw new Error('Browser ini tidak mendukung Web Bluetooth API. Gunakan Chrome/Edge atau mode COM Port (Web Serial).');
        }
        var device = await navigator.bluetooth.requestDevice({
            acceptAllDevices: true,
            optionalServices: BLE_SERVICE_UUIDS
        });
        var server = await device.gatt.connect();
        try {
            var writeChar = null;
            for (var i = 0; i < BLE_SERVICE_UUIDS.length && !writeChar; i++) {
                try {
                    var service = await server.getPrimaryService(BLE_SERVICE_UUIDS[i]);
                    var chars = await service.getCharacteristics();
                    for (var j = 0; j < chars.length; j++) {
                        if (chars[j].properties.write || chars[j].properties.writeWithoutResponse) {
                            writeChar = chars[j];
                            break;
                        }
                    }
                } catch (e) { /* try next service UUID */ }
            }
            if (!writeChar) {
                throw new Error('Printer memakai Bluetooth Classic SPP. Gunakan tombol "Print COM / USB (ESC/POS)" setelah pairing di Windows.');
            }
            var chunkSize = 100;
            for (var offset = 0; offset < payloadBytes.length; offset += chunkSize) {
                var chunk = payloadBytes.slice(offset, offset + chunkSize);
                if (writeChar.properties.writeWithoutResponse) {
                    await writeChar.writeValueWithoutResponse(chunk);
                } else {
                    await writeChar.writeValue(chunk);
                }
            }
        } finally {
            if (device.gatt.connected) {
                device.gatt.disconnect();
            }
        }
    }

    function readReceiptDataFromDom() {
        var box = document.getElementById('thermalReceiptPrintArea');
        if (!box) return {};
        var parsedItems = [];
        try {
            var rawItems = box.getAttribute('data-items');
            if (rawItems) parsedItems = JSON.parse(rawItems);
        } catch (e) {
            parsedItems = [];
        }
        return {
            noStruk: box.getAttribute('data-no-struk') || '-',
            tanggal: box.getAttribute('data-tanggal') || '-',
            kasir: box.getAttribute('data-kasir') || 'Sistem',
            kodeMember: box.getAttribute('data-kode-member') || '-',
            nama: box.getAttribute('data-nama') || '-',
            rumah: box.getAttribute('data-rumah') || '-',
            noHp: box.getAttribute('data-no-hp') || '-',
            layanan: box.getAttribute('data-layanan') || '-',
            periode: box.getAttribute('data-periode') || '-',
            items: parsedItems,
            total: box.getAttribute('data-total') || 'Rp0',
            status: box.getAttribute('data-status') || 'LUNAS'
        };
    }

    document.addEventListener('DOMContentLoaded', function () {
        var btnSerial = document.getElementById('btnPrintEscPosSerial');
        var btnBle = document.getElementById('btnPrintEscPosBle');
        var baudSelect = document.getElementById('escposBaudRate');
        var paperSelect = document.getElementById('escposPaperSize');
        var receiptBox = document.getElementById('thermalReceiptPrintArea');

        function getLineWidth() {
            return (paperSelect && paperSelect.value === '58') ? 32 : 48;
        }

        if (paperSelect && receiptBox) {
            paperSelect.addEventListener('change', function () {
                var is58 = paperSelect.value === '58';
                receiptBox.classList.toggle('paper-58mm', is58);
                receiptBox.classList.toggle('paper-80mm', !is58);
            });
        }

        if (btnSerial) {
            btnSerial.addEventListener('click', async function () {
                try {
                    var bytes = buildEscPosReceipt(readReceiptDataFromDom(), getLineWidth());
                    var baud = baudSelect ? parseInt(baudSelect.value, 10) : 9600;
                    await printViaSerial(bytes, baud);
                    showStatus('Struk berhasil dikirim langsung ke printer thermal (' + (getLineWidth() === 32 ? '58mm' : '80mm') + ').', false);
                } catch (err) {
                    showStatus('Gagal cetak via Serial/COM: ' + (err && err.message ? err.message : err), true);
                }
            });
        }

        if (btnBle) {
            btnBle.addEventListener('click', async function () {
                try {
                    var bytes = buildEscPosReceipt(readReceiptDataFromDom(), getLineWidth());
                    await printViaBluetoothBle(bytes);
                    showStatus('Struk berhasil dikirim langsung ke printer thermal via Bluetooth BLE.', false);
                } catch (err) {
                    showStatus('Gagal cetak via Bluetooth BLE: ' + (err && err.message ? err.message : err), true);
                }
            });
        }
    });
})(window);
