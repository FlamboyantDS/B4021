# Bot Transaksi Semi-Manual B402

Bot ini memungkinkan Anda untuk membuat dan mengirim transaksi ke kontrak B402 Relayer secara manual. Anda dapat menentukan penerima, jumlah, dan token, dan skrip akan menangani pembuatan tanda tangan EIP-712 dan pengiriman transaksi.

## Penafian

**GUNAKAN DENGAN RISIKO ANDA SENDIRI.** Perangkat lunak ini disediakan "sebagaimana adanya" tanpa jaminan. Kontrak pintar yang berinteraksi dengannya belum diaudit secara profesional.

## Latar Belakang

Kontrak NFT yang Anda targetkan (`0xafcd15f17d042ee3db94cdf6530a97bf32a74e02`) adalah kontrak dengan **pasokan tetap**. Ini berarti semua NFT telah dibuat pada saat peluncuran kontrak. Tidak ada fungsi `mint` publik untuk membuat NFT baru.

Semua NFT yang dicetak dikirim ke alamat `0x39Dcdd14A0c40E19Cd8c892fD00E9e7963CD49D3`.

Untuk mendapatkan NFT, Anda harus berinteraksi dengan sistem yang telah mereka siapkan, yang menggunakan kontrak "Relayer" untuk memproses pembayaran. Bot ini membantu Anda berinteraksi dengan kontrak Relayer tersebut.

## Fitur

*   Membuat tanda tangan EIP-712 untuk otorisasi pembayaran B402.
*   Memungkinkan Anda memasukkan detail transaksi secara manual:
    *   Kunci pribadi Anda
    *   Alamat penerima
    *   Jumlah token
    *   Alamat kontrak token
*   Mengirimkan transaksi ke jaringan BSC.

## Prasyarat

*   Python 3.x
*   Dompet BSC dengan dana untuk membayar token (misalnya, 0,1 USDT).

## Instalasi

1.  **Kloning repositori ini:**
    ```bash
    git clone <url-repo>
    cd <nama-repo>
    ```

2.  **Instal dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

## Penggunaan

1.  **Jalankan skrip:**
    ```bash
    python semi_manual_bot.py
    ```

2.  **Masukkan informasi yang diminta:**
    *   **Kunci pribadi Anda:** Kunci pribadi dari dompet BSC Anda. Ini diperlukan untuk menandatangani transaksi.
    *   **Alamat penerima:** Alamat kontrak yang akan menerima pembayaran Anda (USDT) dan memicu transfer NFT. **Anda perlu menemukan alamat ini dengan mengamati transaksi yang berhasil di [BscScan](https://bscscan.com/address/0xE1C2830d5DDd6B49E9c46EbE03a98Cb44CD8eA5a).**
    *   **Jumlah token:** Jumlah token yang akan dikirim (misalnya, `0.1`).
    *   **Alamat kontrak token:** Alamat kontrak token yang ingin Anda gunakan untuk pembayaran (misalnya, alamat USDT di BSC adalah `0x55d398326f99059fF775485246999027B3197955`).

Skrip kemudian akan mengirimkan transaksi dan mencetak hash transaksi setelah selesai.
