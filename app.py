st.experimental_rerun()
    
    elif choice == "Mahsulotlar ro'yxati":
        st.subheader("Mahsulotlar ro'yxati")
        
        if st.session_state.product_data.empty:
            st.info("Hozircha mahsulotlar yo'q. Mahsulotlarni 'Mahsulot qo'shish' sahifasidan qo'shing.")
        else:
            # Filtrlash
            filter_options = st.multiselect("Toifa bo'yicha filtrlash", TOIFALAR)
            
            filtered_data = st.session_state.product_data
            if filter_options:
                filtered_data = filtered_data[filtered_data['toifa'].isin(filter_options)]
            
            # Mahsulotlarni ID bo'yicha guruhlash
            unique_products = filtered_data[['id', 'kod', 'toifa']].drop_duplicates()
            
            for _, product in unique_products.iterrows():
                product_id = product['id']
                product_data = filtered_data[filtered_data['id'] == product_id]
                
                with st.expander(f"Mahsulot: {product['kod']} - {product['toifa']}"):
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        if not pd.isna(product_data['rasm'].iloc[0]):
                            display_image(product_data['rasm'].iloc[0])
                        else:
                            st.info("Rasim mavjud emas")
                    
                    with col2:
                        st.write(f"Kod: {product['kod']}")
                        st.write(f"Toifa: {product['toifa']}")
                        st.write(f"Davlat: {product_data['davlat'].iloc[0]}")
                        st.write(f"Do'kon ID: {product_data['dokon_id'].iloc[0]}")
                        st.write(f"Omborchi: {product_data['omborchi'].iloc[0]}")
                        
                        # Ranglar jadvali
                        st.subheader("Ranglar va o'lchamlar")
                        color_data = []
                        for _, row in product_data.iterrows():
                            color_data.append({
                                'Rang': row['rang'],
                                'O\'lcham': row['olcham'],
                                'Miqdor': row['miqdor'],
                                'Narx (so\'m)': row['narx']
                            })
                        
                        st.table(pd.DataFrame(color_data))
                    
                    # Tahrirlash va o'chirish tugmalari
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Tahrirlash #{product_id}", key=f"edit_{product_id}"):
                            st.info("Tahrirlash funksiyasi hozircha mavjud emas")
                    
                    with col2:
                        if st.button(f"O'chirish #{product_id}", key=f"delete_{product_id}"):
                            st.session_state.product_data = st.session_state.product_data[st.session_state.product_data['id'] != product_id]
                            st.success(f"Mahsulot (ID: {product_id}) muvaffaqiyatli o'chirildi")
                            st.experimental_rerun()
    
    elif choice == "Excel yuklab olish":
        st.subheader("Ma'lumotlarni Excel formatida yuklab olish")
        
        if st.session_state.product_data.empty:
            st.info("Hozircha mahsulotlar yo'q. Mahsulotlarni 'Mahsulot qo'shish' sahifasidan qo'shing.")
        else:
            if st.button("Excel faylni tayyorlash"):
                with st.spinner("Excel fayl tayyorlanmoqda..."):
                    excel_file = save_to_excel(st.session_state.product_data)
                    
                    with open(excel_file, "rb") as f:
                        bytes_data = f.read()

                    st.download_button(
                        label="Excel faylni yuklab olish",
                        data=bytes_data,
                        file_name="omborxona_malumotlari.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    if os.path.exists(excel_file):
                        os.remove(excel_file)

if name == "main":
    main()
