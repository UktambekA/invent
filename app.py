import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image
import os
from datetime import datetime

# Papka yaratish funksiyasi
def create_folders():
    if not os.path.exists("images"):
        os.makedirs("images")
    if not os.path.exists("data"):
        os.makedirs("data")

# Ma'lumotlarni saqlash funksiyasi
def save_data(df, filename="data/inventory_data.csv"):
    df.to_csv(filename, index=False)

# Ma'lumotlarni yuklash funksiyasi
def load_data(filename="data/inventory_data.csv"):
    try:
        return pd.read_csv(filename)
    except FileNotFoundError:
        # Agar fayl topilmasa, yangi DataFrame yaratamiz
        return pd.DataFrame({
            'mahsulot_id': [],
            'mahsulot_nomi': [],
            'rasm_joyi': [],
            'toifa': [],
            'davlat': [],
            'dokon_id': [],
            'omborchi': [],
            'rang': [],
            'olcham': [],
            'miqdor': [],
            'narx': []
        })

# Rasmni saqlash funksiyasi
def save_image(image, product_id):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    image_path = f"images/{product_id}_{timestamp}.jpg"
    image.save(image_path)
    return image_path

# Excel faylni yuklash funksiyasi
def to_excel(df, filename="omborxona_malumotlari.xlsx"):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Barcha ma'lumotlar uchun sheet
    df.to_excel(writer, sheet_name='Barcha_Malumotlar', index=False)
    
    # Toifalar bo'yicha sheets
    toifalar = df['toifa'].unique()
    for toifa in toifalar:
        toifa_df = df[df['toifa'] == toifa]
        toifa_df.to_excel(writer, sheet_name=f'Toifa_{toifa}', index=False)
    
    # Mahsulot ID va rasmlar uchun sheet
    id_rasm_df = df[['mahsulot_id', 'rasm_joyi']].drop_duplicates()
    id_rasm_df.to_excel(writer, sheet_name='ID_va_Rasmlar', index=False)
    
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# Download link funksiyasi
def get_download_link(df, filename="omborxona_malumotlari.xlsx"):
    """Excel faylni yuklab olish uchun link yaratadi"""
    val = to_excel(df)
    b64 = base64.b64encode(val).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Excel faylni yuklab olish</a>'

# Asosiy dastur
def main():
    create_folders()
    
    st.set_page_config(page_title="Omborxona Boshqarish Tizimi", layout="wide")
    
    st.title("Omborxona Boshqarish Tizimi")
    
    # Inventar ma'lumotlarini yuklash
    inventory_data = load_data()
    
    # Sidebar - Amal tanlash
    st.sidebar.title("Boshqarish paneli")
    action = st.sidebar.radio("Tanlang:", ["Mahsulot qo'shish", "Mahsulotlarni ko'rish", "Mahsulotni tahrirlash"])
    
    # Umumiy ma'lumotlar (barcha mahsulotlar uchun bir xil)
    if action in ["Mahsulot qo'shish"]:
        with st.sidebar.expander("Umumiy ma'lumotlar", expanded=True):
            dokon_id = st.text_input("Do'kon ID", value=st.session_state.get('dokon_id', ''))
            omborchi = st.text_input("Omborchi ismi", value=st.session_state.get('omborchi', ''))
            davlat = st.text_input("Ishlab chiqarilgan davlat", value=st.session_state.get('davlat', ''))
            
            # Session state'ga saqlash
            if dokon_id:
                st.session_state['dokon_id'] = dokon_id
            if omborchi:
                st.session_state['omborchi'] = omborchi
            if davlat:
                st.session_state['davlat'] = davlat
    
    # Mahsulot qo'shish
    if action == "Mahsulot qo'shish":
        st.header("Yangi mahsulot qo'shish")
        
        col1, col2 = st.columns(2)
        
        with col1:
            mahsulot_id = st.text_input("Mahsulot kodi", key="m_id")
            mahsulot_nomi = st.text_input("Mahsulot nomi", key="m_nomi")
            toifa = st.selectbox("Toifa", ["Erkaklar", "Ayollar", "Bolalar", "Qizlar"], key="toifa")
            
            # Rasm yuklash
            uploaded_file = st.file_uploader("Mahsulot rasmini yuklang", type=["jpg", "jpeg", "png"])
            if uploaded_file is not None:
                image = Image.open(uploaded_file)
                st.image(image, caption='Yuklangan rasm', width=300)
            
            # Kamera bilan rasm olish
            use_camera = st.checkbox("Kamera bilan rasm olish")
            if use_camera:
                camera_input = st.camera_input("Rasm olish")
                if camera_input is not None:
                    image = Image.open(camera_input)
                    st.image(image, caption='Olingan rasm', width=300)
                    uploaded_file = camera_input
        
        with col2:
            # Ranglar va o'lchamlar
            st.subheader("Ranglar va o'lchamlar")
            
            # Ranglar ro'yxati
            available_colors = ["Qora", "Oq", "Ko'k", "Qizil", "Yashil", "Sariq", "Jigarrang", "Kulrang"]
            
            # Yangi rang qo'shish
            new_color = st.text_input("Yangi rang qo'shish (ixtiyoriy)")
            if new_color and new_color not in available_colors:
                available_colors.append(new_color)
            
            # Tanlangan ranglarni saqlash uchun konteyner
            if 'selected_colors' not in st.session_state:
                st.session_state.selected_colors = []
            
            # Rang tanlash
            selected_color = st.selectbox("Rang tanlang", available_colors)
            
            # O'lchamlar
            olcham_options = ["XS", "S", "M", "L", "XL", "XXL", "XXXL"]
            olcham = st.selectbox("O'lcham", olcham_options)
            miqdor = st.number_input("Miqdor", min_value=0, step=1)
            narx = st.number_input("Narx", min_value=0, step=1000)
            
            # Tanlangan rangni qo'shish
            if st.button("Rang/o'lcham qo'shish"):
                new_item = {
                    "rang": selected_color,
                    "olcham": olcham,
                    "miqdor": miqdor,
                    "narx": narx
                }
                st.session_state.selected_colors.append(new_item)
                st.success(f"Qo'shildi: {selected_color} - {olcham}, {miqdor} dona, {narx} so'm")
            
            # Tanlangan ranglarni ko'rsatish
            if st.session_state.selected_colors:
                st.subheader("Qo'shilgan ranglar va o'lchamlar")
                for i, item in enumerate(st.session_state.selected_colors):
                    st.write(f"{i+1}. {item['rang']} - {item['olcham']}, {item['miqdor']} dona, {item['narx']} so'm")
                
                if st.button("Tanlangan rangni o'chirish"):
                    if st.session_state.selected_colors:
                        st.session_state.selected_colors.pop()
                        st.success("Oxirgi element o'chirildi!")
        
        # Mahsulotni saqlash
        if st.button("Mahsulotni saqlash", key="save_product"):
            if not mahsulot_id or not mahsulot_nomi or not uploaded_file or not st.session_state.selected_colors:
                st.error("Iltimos, barcha zarur ma'lumotlarni to'ldiring!")
            else:
                # Rasmni saqlash
                image = Image.open(uploaded_file)
                image_path = save_image(image, mahsulot_id)
                
                # Yangi qatorlar yaratish
                new_rows = []
                for item in st.session_state.selected_colors:
                    new_rows.append({
                        'mahsulot_id': mahsulot_id,
                        'mahsulot_nomi': mahsulot_nomi,
                        'rasm_joyi': image_path,
                        'toifa': toifa,
                        'davlat': st.session_state.get('davlat', ''),
                        'dokon_id': st.session_state.get('dokon_id', ''),
                        'omborchi': st.session_state.get('omborchi', ''),
                        'rang': item['rang'],
                        'olcham': item['olcham'],
                        'miqdor': item['miqdor'],
                        'narx': item['narx']
                    })
                
                # Ma'lumotlarni yangilash
                new_data = pd.DataFrame(new_rows)
                inventory_data = pd.concat([inventory_data, new_data], ignore_index=True)
                save_data(inventory_data)
                
                st.success("Mahsulot muvaffaqiyatli saqlandi!")
                st.session_state.selected_colors = []  # Ranglar ro'yxatini tozalash
                
                # Formani tozalash (refresh qilish)
                st.experimental_rerun()
    
    # Mahsulotlarni ko'rish
    elif action == "Mahsulotlarni ko'rish":
        st.header("Barcha mahsulotlar")
        
        if inventory_data.empty:
            st.warning("Hozircha ma'lumotlar mavjud emas")
        else:
            # Filtrlar
            col1, col2, col3 = st.columns(3)
            with col1:
                filter_toifa = st.multiselect("Toifa bo'yicha saralash", options=inventory_data['toifa'].unique())
            with col2:
                filter_rang = st.multiselect("Rang bo'yicha saralash", options=inventory_data['rang'].unique())
            with col3:
                filter_olcham = st.multiselect("O'lcham bo'yicha saralash", options=inventory_data['olcham'].unique())
            
            # Filter qo'llash
            filtered_data = inventory_data.copy()
            if filter_toifa:
                filtered_data = filtered_data[filtered_data['toifa'].isin(filter_toifa)]
            if filter_rang:
                filtered_data = filtered_data[filtered_data['rang'].isin(filter_rang)]
            if filter_olcham:
                filtered_data = filtered_data[filtered_data['olcham'].isin(filter_olcham)]
            
            # Natijalarni ko'rsatish
            st.write(f"Jami {len(filtered_data)} ta mahsulot topildi")
            st.dataframe(filtered_data)
            
            # Excel yuklab olish
            st.markdown(get_download_link(filtered_data), unsafe_allow_html=True)
            
            # Mahsulot detallarini ko'rish
            selected_product_id = st.selectbox("Mahsulot detallarini ko'rish", options=filtered_data['mahsulot_id'].unique())
            
            if selected_product_id:
                product_details = filtered_data[filtered_data['mahsulot_id'] == selected_product_id]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"Mahsulot: {product_details['mahsulot_nomi'].iloc[0]}")
                    st.write(f"ID: {selected_product_id}")
                    st.write(f"Toifa: {product_details['toifa'].iloc[0]}")
                    st.write(f"Davlat: {product_details['davlat'].iloc[0]}")
                    st.write(f"Do'kon ID: {product_details['dokon_id'].iloc[0]}")
                    st.write(f"Omborchi: {product_details['omborchi'].iloc[0]}")
                
                with col2:
                    # Rasmni ko'rsatish
                    try:
                        image_path = product_details['rasm_joyi'].iloc[0]
                        if os.path.exists(image_path):
                            image = Image.open(image_path)
                            st.image(image, caption='Mahsulot rasmi', width=300)
                        else:
                            st.warning("Rasm topilmadi")
                    except Exception as e:
                        st.error(f"Rasmni yuklashda xatolik: {e}")
                
                # Rang va o'lchamlar jadvalini ko'rsatish
                st.subheader("Ranglar va o'lchamlar")
                
                # Group by rang and olcham
                colors_df = product_details[['rang', 'olcham', 'miqdor', 'narx']].copy()
                colors_df = colors_df.sort_values(['rang', 'olcham'])
                
                # Show the table
                st.dataframe(colors_df)
    
    # Mahsulotni tahrirlash
    elif action == "Mahsulotni tahrirlash":
        st.header("Mahsulotni tahrirlash")
        
        if inventory_data.empty:
            st.warning("Hozircha ma'lumotlar mavjud emas")
        else:
            # Mahsulot tanlash
            selected_product_id = st.selectbox("Tahrirlash uchun mahsulot tanlang", options=inventory_data['mahsulot_id'].unique())
            
            if selected_product_id:
                product_data = inventory_data[inventory_data['mahsulot_id'] == selected_product_id]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Asosiy ma'lumotlarni tahrirlash
                    st.subheader("Asosiy ma'lumotlar")
                    
                    # Mavjud ma'lumotlarni olish
                    current_name = product_data['mahsulot_nomi'].iloc[0]
                    current_toifa = product_data['toifa'].iloc[0]
                    current_davlat = product_data['davlat'].iloc[0]
                    current_dokon_id = product_data['dokon_id'].iloc[0]
                    current_omborchi = product_data['omborchi'].iloc[0]
                    current_image_path = product_data['rasm_joyi'].iloc[0]
                    
                    # Tahrirlash formasini ko'rsatish
                    new_name = st.text_input("Mahsulot nomi", value=current_name)
                    new_toifa = st.selectbox("Toifa", ["Erkaklar", "Ayollar", "Bolalar", "Qizlar"], index=["Erkaklar", "Ayollar", "Bolalar", "Qizlar"].index(current_toifa))
                    new_davlat = st.text_input("Ishlab chiqarilgan davlat", value=current_davlat)
                    new_dokon_id = st.text_input("Do'kon ID", value=current_dokon_id)
                    new_omborchi = st.text_input("Omborchi ismi", value=current_omborchi)
                    
                    # Rasmni ko'rsatish
                    try:
                        if os.path.exists(current_image_path):
                            image = Image.open(current_image_path)
                            st.image(image, caption='Joriy rasm', width=300)
                        else:
                            st.warning("Rasm topilmadi")
                    except Exception as e:
                        st.error(f"Rasmni yuklashda xatolik: {e}")
                    
                    # Yangi rasm yuklash
                    new_image = st.file_uploader("Yangi rasm (ixtiyoriy)", type=["jpg", "jpeg", "png"])
                    
                    # Kamera bilan rasm olish
                    use_camera = st.checkbox("Kamera bilan yangi rasm olish")
                    if use_camera:
                        camera_input = st.camera_input("Rasm olish")
                        if camera_input is not None:
                            new_image = camera_input
                
                with col2:
                    # Rang va o'lchamlarni tahrirlash
                    st.subheader("Ranglar va o'lchamlar")
                    
                    # Mavjud rang/o'lchamlarni ko'rsatish
                    unique_color_sizes = product_data[['rang', 'olcham', 'miqdor', 'narx']].drop_duplicates()
                    
                    # Rang va o'lcham tanlash
                    selected_row_index = st.selectbox(
                        "Tahrirlash uchun qatorni tanlang", 
                        range(len(unique_color_sizes)), 
                        format_func=lambda i: f"{unique_color_sizes.iloc[i]['rang']} - {unique_color_sizes.iloc[i]['olcham']}, {unique_color_sizes.iloc[i]['miqdor']} dona, {unique_color_sizes.iloc[i]['narx']} so'm"
                    )
                    
                    if selected_row_index is not None:
                        selected_row = unique_color_sizes.iloc[selected_row_index]
                        
                        # Tahrirlash formasi
                        new_rang = st.text_input("Rang", value=selected_row['rang'])
                        new_olcham = st.selectbox("O'lcham", ["XS", "S", "M", "L", "XL", "XXL", "XXXL"], index=["XS", "S", "M", "L", "XL", "XXL", "XXXL"].index(selected_row['olcham']) if selected_row['olcham'] in ["XS", "S", "M", "L", "XL", "XXL", "XXXL"] else 0)
                        new_miqdor = st.number_input("Miqdor", min_value=0, step=1, value=int(selected_row['miqdor']))
                        new_narx = st.number_input("Narx", min_value=0, step=1000, value=int(selected_row['narx']))
                        
                        # Saqlash tugmasi
                        if st.button("Rang/o'lcham o'zgarishlarini saqlash"):
                            # Filter the rows that need to be updated
                            mask = (
                                (inventory_data['mahsulot_id'] == selected_product_id) & 
                                (inventory_data['rang'] == selected_row['rang']) & 
                                (inventory_data['olcham'] == selected_row['olcham'])
                            )
                            
                            # Update the values
                            inventory_data.loc[mask, 'rang'] = new_rang
                            inventory_data.loc[mask, 'olcham'] = new_olcham
                            inventory_data.loc[mask, 'miqdor'] = new_miqdor
                            inventory_data.loc[mask, 'narx'] = new_narx
                            
                            # Save the updated data
                            save_data(inventory_data)
                            st.success("Ranglar va o'lchamlar muvaffaqiyatli yangilandi!")
                            st.experimental_rerun()
                    
                    # Yangi rang/o'lcham qo'shish
                    st.subheader("Yangi rang/o'lcham qo'shish")
                    
                    # Ranglar ro'yxati
                    available_colors = ["Qora", "Oq", "Ko'k", "Qizil", "Yashil", "Sariq", "Jigarrang", "Kulrang"]
                    unique_colors = product_data['rang'].unique()
                    for color in unique_colors:
                        if color not in available_colors:
                            available_colors.append(color)
                    
                    add_color = st.selectbox("Rang", available_colors)
                    add_olcham = st.selectbox("O'lcham", ["XS", "S", "M", "L", "XL", "XXL", "XXXL"])
                    add_miqdor = st.number_input("Miqdor", min_value=0, step=1, key="add_miqdor")
                    add_narx = st.number_input("Narx", min_value=0, step=1000, key="add_narx")
                    
                    if st.button("Yangi rang/o'lcham qo'shish"):
                        # Yangi qator yaratish
                        new_row = {
                            'mahsulot_id': selected_product_id,
                            'mahsulot_nomi': current_name,
                            'rasm_joyi': current_image_path,
                            'toifa': current_toifa,
                            'davlat': current_davlat,
                            'dokon_id': current_dokon_id,
                            'omborchi': current_omborchi,
                            'rang': add_color,
                            'olcham': add_olcham,
                            'miqdor': add_miqdor,
                            'narx': add_narx
                        }
                        
                        # Inventar ma'lumotlariga qo'shish
                        inventory_data = pd.concat([inventory_data, pd.DataFrame([new_row])], ignore_index=True)
                        save_data(inventory_data)
                        st.success("Yangi rang/o'lcham qo'shildi!")
                        st.experimental_rerun()
                
                # Barcha o'zgarishlarni saqlash
                if st.button("Asosiy ma'lumotlarni saqlash"):
                    # Rasmni yangilash
                    if new_image is not None:
                        image = Image.open(new_image)
                        new_image_path = save_image(image, selected_product_id)
                    else:
                        new_image_path = current_image_path
                    
                    # Filter the rows that need to be updated
                    mask = (inventory_data['mahsulot_id'] == selected_product_id)
                    
                    # Update the values
                    inventory_data.loc[mask, 'mahsulot_nomi'] = new_name
                    inventory_data.loc[mask, 'toifa'] = new_toifa
                    inventory_data.loc[mask, 'davlat'] = new_davlat
                    inventory_data.loc[mask, 'dokon_id'] = new_dokon_id
                    inventory_data.loc[mask, 'omborchi'] = new_omborchi
                    inventory_data.loc[mask, 'rasm_joyi'] = new_image_path
                    
                    # Save the updated data
                    save_data(inventory_data)
                    st.success("Mahsulot ma'lumotlari muvaffaqiyatli yangilandi!")
                    
                    # Update session state
                    st.session_state['davlat'] = new_davlat
                    st.session_state['dokon_id'] = new_dokon_id
                    st.session_state['omborchi'] = new_omborchi
                    
                    # Refresh page
                    st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("© 2025 Omborxona Boshqarish Tizimi")

if __name__ == "__main__":
    main()
