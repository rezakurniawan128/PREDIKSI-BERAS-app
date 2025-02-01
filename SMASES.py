import pandas as pd  
import numpy as np  
import matplotlib.pyplot as plt  
import streamlit as st  
from statsmodels.tsa.holtwinters import SimpleExpSmoothing  

# 1. Upload Excel file  
st.title("Prediksi Harga Beras Menggunakan Single Moving Average & Single Exponential Smoothing")  
uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])  
  
if uploaded_file is not None:  
    # 2. Load Excel file  
    data = pd.read_excel(uploaded_file)  
    
    # 3. Tampilkan daftar jenis beras yang tersedia  
    st.write("Kolom harga beras yang tersedia:")  
    price_columns = data.columns[2:]  # Kolom harga mulai dari kolom ke-3  
    for i, col in enumerate(price_columns, start=1):  
        st.write(f"{i}. {col}")  
    
    # 4. Pilih jenis beras  
    choice = st.selectbox("Pilih nomor kolom beras yang ingin dianalisis:", range(1, len(price_columns) + 1))  
    price_column = price_columns[choice - 1]  
    
    # 5. Proses data  
    data['day_of_year'] = np.arange(1, len(data) + 1)  
    data = data[['month', 'Tanggal', 'day_of_year', price_column]].rename(columns={price_column: 'price'})  
    
    # 6. Hapus data ekstrem (harga < 12000)  
    data = data[data['price'] >= 12000]  
    
    # 7. Pastikan ada cukup data setelah filter harga  
    if data.empty:  
        st.error("Setelah memfilter harga < 12000, tidak ada data yang tersisa. Periksa kembali dataset.")  
    else:  
        # 8. Tampilkan ringkasan data  
        summary_data = {
            'Rata-Rata Harga': [data['price'].mean()],
            'Harga Minimum': [data['price'].min()],
            'Harga Maksimum': [data['price'].max()],
            'Jumlah Data': [len(data)]
        }
        summary_table = pd.DataFrame(summary_data)
        st.subheader("Ringkasan Data")
        st.write(summary_table)
        
        # 9. Slider untuk memilih horizon prediksi untuk SMA  
        sma_horizon = st.selectbox("Pilih horizon prediksi untuk SMA:", [7, 14, 30])
        
        # 10. Select slider untuk memilih parameter SES dengan opsi spesifik
        ses_alpha = st.select_slider("Pilih parameter alpha untuk SES:", 
                                   options=[0.2, 0.5, 0.8])
    
        # 11. Hitung Single Moving Average (SMA)  
        window_size = 30  # Menggunakan window 30 hari untuk SMA  
        data['SMA'] = data['price'].rolling(window=window_size).mean()

        # 12. Hitung Single Exponential Smoothing (SES) dengan alpha yang dapat diubah
        if len(data) >= 2:
            # Buat model SES baru setiap kali alpha berubah
            ses_model = SimpleExpSmoothing(data['price'])
            fit_model = ses_model.fit(smoothing_level=ses_alpha, optimized=False)
            
            # Simpan hasil fitting dan forecast
            data['SES'] = fit_model.fittedvalues
            ses_forecast = fit_model.forecast(steps=sma_horizon)
            
            # Tampilkan informasi model SES
            st.write(f"Alpha yang digunakan: {ses_alpha}")
        else:  
            st.warning("Tidak cukup data untuk melakukan Single Exponential Smoothing.")  
            ses_forecast = None  

        # 13. Prediksi SMA secara iteratif
        sma_predictions = []
        if not data['SMA'].isnull().all():
            sma_last_values = data['SMA'].dropna().iloc[-window_size:].tolist()
            for _ in range(sma_horizon):
                next_sma = np.mean(sma_last_values[-window_size:])
                sma_predictions.append(next_sma)
                sma_last_values.append(next_sma)
        else:
            sma_predictions = [None] * sma_horizon

        # 14. Tampilkan tabel hasil prediksi dengan perbandingan
        st.subheader("Hasil Prediksi")
        results = pd.DataFrame({
            'Horizon (Hari)': list(range(1, sma_horizon + 1)),
            'Harga Asli': data['price'].iloc[-sma_horizon:].tolist() if len(data) >= sma_horizon else [None] * sma_horizon,
            'Prediksi SMA': sma_predictions,
            'Prediksi SES': ses_forecast.values if ses_forecast is not None else [None] * sma_horizon
        })
        st.write(results)

        # 15. Plot hasil dengan clear_figure
        plt.clf()  # Clear figure sebelum plotting baru
        plt.figure(figsize=(14, 6))
        plt.plot(data['day_of_year'], data['price'], label='Harga Asli', color='black')
        
        # Plot historical fitted values
        plt.plot(data['day_of_year'], data['SES'], label=f'SES Fitted (α={ses_alpha})', color='orange')
        
        if sma_predictions:
            plt.plot(
                range(len(data) + 1, len(data) + 1 + sma_horizon),
                sma_predictions,
                color='blue',
                linestyle='--',
                label='Prediksi SMA'
            )
        if ses_forecast is not None:
            plt.plot(
                range(len(data) + 1, len(data) + 1 + sma_horizon),
                ses_forecast,
                color='red',
                linestyle='--',
                label='Prediksi SES'
            )
        plt.title(f'Hasil Prediksi Harga Beras - {price_column}')
        plt.xlabel('Hari ke-')
        plt.ylabel('Harga')
        plt.legend()
        st.pyplot(plt)