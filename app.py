
        import streamlit as st
import pandas as pd
import io
import base64
from PIL import Image
from datetime import datetime
import os
import uuid

# Loyihaning papka strukturasini yaratish
def setup_directories():
    if not os.path.exists("images"):
        os.makedirs("images")
    if not os.path.exists("data"):
        os.makedirs("data")

# Ma'lumotlarni saqlash
def save_data(df):
    df.to_csv("data/inventory_data.csv", index=False)

# Ma'lumotlarni yuklash
def load_data():
    try:
        return pd.read_csv("data/inventory_data.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            'product_id', 'product_name', 'category', 'country_of_origin', 
            'store_id', 'warehouse_manager', 'image_path', 'colors_sizes_quantity', 'price'
        ])

# Rasm yuklash
def save_uploaded_image(uploaded_file):
    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        img_path = os.path.join("images", unique_filename)
        
        with open(img_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return img_path
    return None

# Rasm ko'rsatish
def display_image(image_path):
    if image_path and os.path.exists(image_path):
        img = Image.open(image_path)
        st.image(img, width=200)
    else:
        st.write("Rasm mavjud emas")

# Excel fayl yaratish va yuklab olish
def create_excel_download_link(df):
    output = io.BytesIO()
    
    # Use pandas to export directly to BytesIO
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Barcha mahsulotlar uchun umumiy ma'lumotlar
        df.to_excel(writer, sheet_name='Barcha_Mahsulotlar', index=False)
        
        # Toifalar bo'yicha ma'lumotlar
        for category in df['category'].unique():
            category_df = df[df['category'] == category]
            category_df.to_excel(writer, sheet_name=f"{category[:30]}", index=False)
        
        # Mahsulot ID va rasm yo'llari uchun alohida sheet
        id_images_df = df[['product_id', 'product_name', 'image_path']]
        id_images_df.to_excel(writer, sheet_name='Mahsulot_ID_Rasmlar', index=False)
    
    b64 = base64.b64encode(output.getvalue()).decode()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="ombor_malumotlari_{current_time}.xlsx">Excel faylni yuklab olish</a>'

# Rang va o'lcham ma'lumotlarini formatlash
def format_colors_sizes(colors_dict):
    result = []
    for color, sizes in colors_dict.items():
        size_str = ", ".join([f"{size}-{qty}" for size, qty in sizes.items()])
        result.append(f"{color}: {size_str}")
    return "; ".join(result)

# Saqlangan rang va o'lcham ma'lumotlarini qayta ishlash
def parse_colors_sizes(colors_sizes_str):
    colors_dict = {}
    if pd.isna(colors_sizes_str):
        return colors_dict
    
    color_blocks = colors_sizes_str.split("; ")
    for block in color_blocks:
        if ":" in block:
            color, sizes_str = block.split(":", 1)
            color = color.strip()
            colors_dict[color] = {}
            
            if sizes_str.strip():
                size_qty_pairs = sizes_str.strip().split(", ")
                for pair in size_qty_pairs:
                    if "-" in pair:
                        size, qty = pair.split("-", 1)
                        colors_dict[color][size.strip()] = int(qty.strip())
    
    return colors_dict

# Statistika sahifasi
def stats_page(df):
    st.header("Omborxona statistikasi")
    
    if df.empty:
        st.info("Statistika uchun ma'lumot mavjud emas.")
        return
    
    # Umumiy mahsulotlar soni
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Jami mahsulotlar", len(df))
    
    with col2:
        # Umumiy miqdorlarni hisoblash
        total_items = 0
        for _, row in df.iterrows():
            colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
            for color, sizes in colors_dict.items():
                for size, qty in sizes.items():
                    total_items += qty
        st.metric("Jami mahsulot birliklari", total_items)
    
    with col3:
        # Jami qiymat
        total_value = 0
        for _, row in df.iterrows():
            colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
            item_count = 0
            for color, sizes in colors_dict.items():
                for size, qty in sizes.items():
                    item_count += qty
            total_value += item_count * row['price']
        
        st.metric("Jami qiymat", f"{total_value:,.0f} so'm")
    
    # Toifalar bo'yicha statistika
    st.subheader("Toifalar bo'yicha statistika")
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Toifa', 'Mahsulotlar soni']
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(category_counts)
    
    with col2:
        st.bar_chart(category_counts.set_index('Toifa'))
    
    # Rang va o'lcham bo'yicha statistika
    st.subheader("Ranglar va o'lchamlar statistikasi")
    
    # Ranglar va o'lchamlar sonini hisoblash
    color_counts = {}
    size_counts = {}
    
    for _, row in df.iterrows():
        colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
        for color, sizes in colors_dict.items():
            if color not in color_counts:
                color_counts[color] = 0
            
            for size, qty in sizes.items():
                if size not in size_counts:
                    size_counts[size] = 0
                
                color_counts[color] += qty
                size_counts[size] += qty
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Ranglar bo'yicha miqdorlar")
        color_df = pd.DataFrame({
            'Rang': list(color_counts.keys()),
            'Miqdor': list(color_counts.values())
        }).sort_values('Miqdor', ascending=False)
        
        st.dataframe(color_df)
    
    with col2:
        st.write("O'lchamlar bo'yicha miqdorlar")
        size_df = pd.DataFrame({
            'O\'lcham': list(size_counts.keys()),
            'Miqdor': list(size_counts.values())
        }).sort_values('Miqdor', ascending=False)
        
        st.dataframe(size_df)
    
    # Omborchilar statistikasi
    st.subheader("Omborchilar statistikasi")
    manager_counts = df['warehouse_manager'].value_counts().reset_index()
    manager_counts.columns = ['Omborchi', 'Mahsulotlar soni']
    
    st.dataframe(manager_counts)
    
    # Excel yuklab olish
    st.markdown(create_excel_download_link(df), unsafe_allow_html=True)

# Asosiy ilova
def main():
    setup_directories()
    
    st.set_page_config(page_title="Omborxona Boshqaruv Tizimi", layout="wide")
    st.title("Omborxona Boshqaruv Tizimi")
    
    # Asosiy ma'lumotlar
    df = load_data()
    
    # Sessiya holati
    if 'editing_product_id' not in st.session_state:
        st.session_state.editing_product_id = None
    
    if 'colors_data' not in st.session_state:
        st.session_state.colors_data = {}
    
    # Sidebar menyu
    st.sidebar.title("Boshqaruv paneli")
    menu = st.sidebar.radio("Menu", ["Mahsulotlarni ko'rish", "Mahsulot qo'shish/tahrirlash"])
    
    # Do'kon va omborchi ma'lumotlari
    with st.sidebar.expander("Do'kon ma'lumotlari"):
        store_id = st.text_input("Do'kon ID")
        warehouse_manager = st.text_input("Omborchi ismi")
        country_of_origin = st.text_input("Ishlab chiqarilgan davlat")
    
    if menu == "Mahsulotlarni ko'rish":
        st.header("Barcha mahsulotlar")
        
        if not df.empty:
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_category = st.multiselect("Toifa bo'yicha filtrlash", options=df['category'].unique())
            
            with col2:
                search_term = st.text_input("Qidirish (mahsulot nomi yoki ID)")
            
            # Apply filters
            filtered_df = df.copy()
            if filter_category:
                filtered_df = filtered_df[filtered_df['category'].isin(filter_category)]
            
            if search_term:
                search_mask = (
                    filtered_df['product_name'].str.contains(search_term, case=False, na=False) | 
                    filtered_df['product_id'].str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[search_mask]
            
            # Display products
            if not filtered_df.empty:
                for _, row in filtered_df.iterrows():
                    col1, col2, col3 = st.columns([1, 2, 1])
                    
                    with col1:
                        display_image(row['image_path'])
                    
                    with col2:
                        st.subheader(row['product_name'])
                        st.write(f"**ID:** {row['product_id']}")
                        st.write(f"**Toifa:** {row['category']}")
                        st.write(f"**Ishlab chiqarilgan davlat:** {row['country_of_origin']}")
                        st.write(f"**Do'kon ID:** {row['store_id']}")
                        st.write(f"**Omborchi:** {row['warehouse_manager']}")
                        st.write(f"**Narxi:** {row['price']}")
                        
                        st.write("**Rang va o'lchamlar:**")
                        colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
                        for color, sizes in colors_dict.items():
                            sizes_str = ", ".join([f"{size}: {qty} dona" for size, qty in sizes.items()])
                            st.write(f"- {color}: {sizes_str}")
                    
                    with col3:
                        if st.button(f"Tahrirlash", key=f"edit_{row['product_id']}"):
                            st.session_state.editing_product_id = row['product_id']
                            st.session_state.colors_data = parse_colors_sizes(row['colors_sizes_quantity'])
                            st.experimental_rerun()
                        
                        if st.button(f"O'chirish", key=f"delete_{row['product_id']}"):
                            df = df[df['product_id'] != row['product_id']]
                            save_data(df)
                            st.success("Mahsulot o'chirildi!")
                            st.experimental_rerun()
                    
                    st.markdown("---")
                
                # Excel ga yuklab olish tugmasi
                st.markdown(create_excel_download_link(filtered_df), unsafe_allow_html=True)
            else:
                st.warning("Qidirish natijasi bo'yicha mahsulot topilmadi.")
        else:
            st.info("Hozircha mahsulotlar mavjud emas. Iltimos, yangi mahsulot qo'shing.")
    
    elif menu == "Mahsulot qo'shish/tahrirlash":
        if st.session_state.editing_product_id:
            st.header("Mahsulotni tahrirlash")
            product_data = df[df['product_id'] == st.session_state.editing_product_id].iloc[0]
        else:
            st.header("Yangi mahsulot qo'shish")
            product_data = pd.Series({
                'product_id': str(uuid.uuid4())[:8],
                'product_name': "",
                'category': "",
                'country_of_origin': country_of_origin,
                'store_id': store_id,
                'warehouse_manager': warehouse_manager,
                'image_path': "",
                'colors_sizes_quantity': "",
                'price': 0
            })
        
        col1, col2 = st.columns(2)
        with col1:
            product_id = st.text_input("Mahsulot ID", value=product_data['product_id'], disabled=True)
            product_name = st.text_input("Mahsulot nomi", value=product_data['product_name'])
            category = st.selectbox("Toifa", options=["Ayollar", "Erkaklar", "Bolalar", "Qizlar"], index=0 if product_data['category'] == "" else ["Ayollar", "Erkaklar", "Bolalar", "Qizlar"].index(product_data['category']))
            uploaded_file = st.file_uploader("Mahsulot rasmi", type=["jpg", "png", "jpeg"])
            price = st.number_input("Narx", value=float(product_data['price']) if product_data['price'] else 0.0, step=1000.0)
        
        with col2:
            if st.session_state.editing_product_id and product_data['image_path'] and os.path.exists(product_data['image_path']):
                st.write("Joriy rasm:")
                display_image(product_data['image_path'])
            
            # Rang va o'lchamlar boshqaruvi
            st.subheader("Rang va o'lchamlar")
            
            available_colors = ["Qora", "Oq", "Ko'k", "Qizil", "Yashil", "Jigarrang", "Sariq", "Kulrang", "Pushti", "Boshqa"]
            available_sizes = ["XS", "S", "M", "L", "XL", "XXL", "XXXL", "Bir o'lcham"]
            
            # Rang qo'shish
            col_color, col_add = st.columns([3, 1])
            with col_color:
                new_color = st.selectbox("Rang tanlang", options=available_colors)
            
            with col_add:
                st.write("")
                st.write("")
                if st.button("Rang qo'shish"):
                    if new_color not in st.session_state.colors_data:
                        st.session_state.colors_data[new_color] = {}
            
            # Mavjud ranglar va o'lchamlar
            for color in list(st.session_state.colors_data.keys()):
                st.markdown(f"**{color}**")
                col_size, col_qty, col_remove = st.columns([2, 1, 1])
                
                with col_size:
                    new_size = st.selectbox(f"O'lcham ({color})", options=available_sizes, key=f"size_{color}")
                
                with col_qty:
                    new_qty = st.number_input(f"Miqdor", min_value=0, step=1, key=f"qty_{color}")
                
                with col_remove:
                    if st.button("Qo'shish", key=f"add_size_{color}"):
                        st.session_state.colors_data[color][new_size] = new_qty
                        st.experimental_rerun()
                
                # O'lchamlarni ko'rsatish
                if st.session_state.colors_data[color]:
                    size_cols = st.columns(len(st.session_state.colors_data[color]) if len(st.session_state.colors_data[color]) > 0 else 1)
                    for i, (size, qty) in enumerate(st.session_state.colors_data[color].items()):
                        with size_cols[i % len(size_cols)]:
                            st.write(f"{size}: {qty} dona")
                            if st.button(f"O'chirish", key=f"remove_{color}_{size}"):
                                del st.session_state.colors_data[color][size]
                                if not st.session_state.colors_data[color]:  # Agar rangning o'lchamlari qolmasa
                                    del st.session_state.colors_data[color]
                                st.experimental_rerun()
                
                st.markdown("---")
        
        # Saqlash tugmasi
        if st.button("Saqlash"):
            # Majburiy maydonlarni tekshirish
            if not product_name:
                st.error("Mahsulot nomini kiriting!")
                return
            
            if not st.session_state.colors_data:
                st.error("Kamida bitta rang va o'lcham qo'shing!")
                return
            
            # Rasm yo'li
            image_path = product_data['image_path']
            if uploaded_file:
                image_path = save_uploaded_image(uploaded_file)
            
            # Rang va o'lchamlar formatini tayyorlash
            colors_sizes_quantity = format_colors_sizes(st.session_state.colors_data)
            
            # Yangi ma'lumotlar
            new_data = {
                'product_id': product_id,
                'product_name': product_name,
                'category': category,
                'country_of_origin': country_of_origin,
                'store_id': store_id,
                'warehouse_manager': warehouse_manager,
                'image_path': image_path,
                'colors_sizes_quantity': colors_sizes_quantity,
                'price': price
            }
            
            # Ma'lumotlarni yangilash yoki qo'shish
            if st.session_state.editing_product_id:
                df.loc[df['product_id'] == st.session_state.editing_product_id] = new_data
                success_message = "Mahsulot muvaffaqiyatli yangilandi!"
            else:
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                success_message = "Yangi mahsulot muvaffaqiyatli qo'shildi!"
            
            # Ma'lumotlarni saqlash
            save_data(df)
            
            # Sessiya holatini qayta o'rnatish
            st.session_state.editing_product_id = None
            st.session_state.colors_data = {}
            
            st.success(success_message)
            st.experimental_rerun()
        
        # Bekor qilish tugmasi
        if st.session_state.editing_product_id and st.button("Bekor qilish"):
            st.session_state.editing_product_id = None
            st.session_state.colors_data = {}
            st.experimental_rerun()

# Statistika sahifasi
def stats_page(df):
    st.header("Omborxona statistikasi")
    
    if df.empty:
        st.info("Statistika uchun ma'lumot mavjud emas.")
        return
    
    # Umumiy mahsulotlar soni
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Jami mahsulotlar", len(df))
    
    with col2:
        # Umumiy miqdorlarni hisoblash
        total_items = 0
        for _, row in df.iterrows():
            colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
            for color, sizes in colors_dict.items():
                for size, qty in sizes.items():
                    total_items += qty
        st.metric("Jami mahsulot birliklari", total_items)
    
    with col3:
        # Jami qiymat
        total_value = 0
        for _, row in df.iterrows():
            colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
            item_count = 0
            for color, sizes in colors_dict.items():
                for size, qty in sizes.items():
                    item_count += qty
            total_value += item_count * row['price']
        
        st.metric("Jami qiymat", f"{total_value:,.0f} so'm")
    
    # Toifalar bo'yicha statistika
    st.subheader("Toifalar bo'yicha statistika")
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Toifa', 'Mahsulotlar soni']
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.dataframe(category_counts)
    
    with col2:
        st.bar_chart(category_counts.set_index('Toifa'))
    
    # Rang va o'lcham bo'yicha statistika
    st.subheader("Ranglar va o'lchamlar statistikasi")
    
    # Ranglar va o'lchamlar sonini hisoblash
    color_counts = {}
    size_counts = {}
    
    for _, row in df.iterrows():
        colors_dict = parse_colors_sizes(row['colors_sizes_quantity'])
        for color, sizes in colors_dict.items():
            if color not in color_counts:
                color_counts[color] = 0
            
            for size, qty in sizes.items():
                if size not in size_counts:
                    size_counts[size] = 0
                
                color_counts[color] += qty
                size_counts[size] += qty
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Ranglar bo'yicha miqdorlar")
        color_df = pd.DataFrame({
            'Rang': list(color_counts.keys()),
            'Miqdor': list(color_counts.values())
        }).sort_values('Miqdor', ascending=False)
        
        st.dataframe(color_df)
    
    with col2:
        st.write("O'lchamlar bo'yicha miqdorlar")
        size_df = pd.DataFrame({
            'O\'lcham': list(size_counts.keys()),
            'Miqdor': list(size_counts.values())
        }).sort_values('Miqdor', ascending=False)
        
        st.dataframe(size_df)
    
    # Omborchilar statistikasi
    st.subheader("Omborchilar statistikasi")
    manager_counts = df['warehouse_manager'].value_counts().reset_index()
    manager_counts.columns = ['Omborchi', 'Mahsulotlar soni']
    
    st.dataframe(manager_counts)
    
    # Excel yuklab olish
    st.markdown(create_excel_download_link(df), unsafe_allow_html=True)

# Ilova ishga tushirish
if __name__ == "__main__":
    # Sidebar menu
    st.sidebar.title("Omborxona tizimi")
    app_menu = st.sidebar.selectbox("Bo'lim", ["Asosiy sahifa", "Statistika"])
    
    # Ma'lumotlarni yuklash
    inventory_data = load_data()
    
    if app_menu == "Asosiy sahifa":
        main()
    elif app_menu == "Statistika":
        stats_page(inventory_data)
