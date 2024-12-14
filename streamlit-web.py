import streamlit as st
import pandas as pd
from spmf import Spmf

# Fungsi untuk menjalankan analisis SPADE
def run_spade_analysis(uploaded_file, min_sup, min_conf, min_lift):
    # Membaca data dari file Excel
    data_read = pd.read_excel(uploaded_file)
    data_read = data_read.sort_values(by=["Transactional_Id", "Sequence_Id"])
    
    # Preprocessing untuk mengubah data ke format SPMF
    transactions = []
    current_transaction = []
    for i, row in data_read.iterrows():
        item = row["Items"]
        event_id = row["Event_Id"]

        if event_id == 1 and current_transaction:
            transactions.append(current_transaction)
            current_transaction = []

        current_transaction.append(str(item))

    if current_transaction:
        transactions.append(current_transaction)

    # Menyimpan data ke file untuk SPMF
    with open("data_spmf.txt", "w") as f:
        for transaction in transactions:
            f.write(" -1 ".join(transaction) + " -1 -2\n")

    # Menjalankan algoritma SPADE
    spmf = Spmf("SPADE", input_filename="data_spmf.txt", output_filename="output_spade.txt", spmf_bin_location_dir="spmf", arguments=[min_sup])
    spmf.run()

    # Membaca hasil analisis
    with open("output_spade.txt", "r") as f:
        patterns = f.readlines()

    # Menghitung support, confidence, dan lift
    pattern_supports = []
    for pattern in patterns:
        parts = pattern.strip().split(" -1 #SUP: ")
        items = list(map(int, parts[0].split(" -1 ")))
        support = int(parts[1])
        pattern_supports.append({"items": items, "support": support})

    with open("data_spmf.txt", "r") as f:
        total_transactions = sum(1 for line in f if line.strip() and "-2" in line)

    filtered_patterns = []
    conclusions = []
    item_mapping = {
    1: "Bacaros",
    2: "Je Premium",
    3: "Armor",
    4: "Oel Steel",
    5: "Boss Ar",
    6: "Fortune",
    7: "Haizelia"
}
    
    for pattern in pattern_supports:
        if len(pattern["items"]) == 2:
            item_1, item_2 = pattern["items"]
            support_ab = pattern["support"]

            support_a = next((p["support"] for p in pattern_supports if p["items"] == [item_1]), 0)
            support_b = next((p["support"] for p in pattern_supports if p["items"] == [item_2]), 0)

            confidence = support_ab / support_a if support_a != 0 else 0
            lift = confidence / (support_b / total_transactions) if support_b != 0 else 0

            item_a = item_mapping.get(item_1)
            item_b = item_mapping.get(item_2)

            if confidence >= min_conf and lift >= min_lift:
                conclusion_text = (
                     f"Jika parfum {item_a} terjual terbanyak dalam 1 hari maka, kemungkinan besar pembeli akan membeli parfum {item_b} "
                     f"dengan keyakinan sebesar {round(confidence, 2) * 100}% dan hubungan sebesar (lift: {round(lift, 2)})."
                )
                filtered_patterns.append({
                    "Pola Aturan": f"{item_a} -> {item_b}",
                    "Support A": support_a,
                    "Support B": support_b,
                    "Support (A, B)": support_ab,
                    "Confidence": f"{round(confidence, 2) * 100}%",
                    "Lift": round(lift, 2)
                })
                conclusions.append(conclusion_text)

    output_df = pd.DataFrame(filtered_patterns)
    return output_df, conclusions

# Streamlit UI
st.title("Analisis Tren Penjualan Parfum")
st.subheader("Unggah file Excel untuk memulai analisis")

# Nilai parameter tetap (tidak dapat diubah pengguna)
min_sup = 0.5
min_conf = 0.8
min_lift = 0.95

# Upload file
uploaded_file = st.file_uploader("Unggah file Excel", type=["xlsx"])

if uploaded_file:
    if st.button("Jalankan Analisis"):
        with st.spinner("Memproses data..."):
            try:
                # Jalankan analisis
                output_df, conclusions = run_spade_analysis(uploaded_file, min_sup, min_conf, min_lift)
                
                st.success("Analisis selesai!")
                st.subheader("Hasil Analisis")
                st.dataframe(output_df)

                # Menampilkan kesimpulan
                st.subheader("Kesimpulan:")
                for conclusion in conclusions:
                    st.write("- ", conclusion)

                # Tombol unduh hasil analisis
                output_file = "hasil_analisis.xlsx"
                output_df.to_excel(output_file, index=False)
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="Download Hasil Analisis",
                        data=file,
                        file_name="hasil_analisis.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")