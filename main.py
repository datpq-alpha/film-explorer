import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


# ==========================================
# LỚP XỬ LÝ DỮ LIỆU (DATA LOADER)
# ==========================================
class DataLoader:
    """Lớp chịu trách nhiệm đọc và làm sạch dữ liệu từ file CSV."""

    @staticmethod
    @st.cache_data
    def load_and_clean_data(filepath):
        # 1. Đọc file thô
        df = pd.read_csv(filepath)

        # 2. Xử lý giá trị "null" dạng chuỗi thành NaN thực sự của numpy
        df.replace("null", np.nan, inplace=True)

        # 3. Xử lý cột Release Date và tạo cột Year
        df['Release Date'] = pd.to_datetime(df['Release Date'], errors='coerce')
        df['Year'] = df['Release Date'].dt.year

        # 4. Xử lý thiếu giá trị ở Major Genre
        df['Major Genre'] = df['Major Genre'].fillna('Unknown')

        # 5. Ép kiểu các cột số liệu (Doanh thu, Kinh phí, Điểm số)
        numeric_cols = ['US Gross', 'Worldwide Gross', 'Production Budget', 'IMDB Rating']
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 6. Loại bỏ các dòng không xác định được năm sản xuất để thanh trượt (slider) hoạt động tốt
        df = df.dropna(subset=['Year'])
        df['Year'] = df['Year'].astype(int)

        return df


# ==========================================
# LỚP VẼ BIỂU ĐỒ (CHART DRAWER)
# ==========================================
class ChartDrawer:
    """Lớp chịu trách nhiệm khởi tạo và hiển thị các biểu đồ phân tích."""

    @staticmethod
    def draw_movies_per_year(df):
        st.subheader("Số lượng phim theo năm")
        if not df.empty:
            year_counts = df['Year'].value_counts().sort_index()
            st.bar_chart(year_counts)
        else:
            st.info("Không có dữ liệu để hiển thị.")

    @staticmethod
    def draw_imdb_distribution(df):
        st.subheader("Phân bố điểm IMDB")
        valid_data = df.dropna(subset=['IMDB Rating'])
        if not valid_data.empty:
            # Sử dụng Altair để vẽ Histogram cho điểm IMDB
            chart = alt.Chart(valid_data).mark_bar().encode(
                alt.X("IMDB Rating:Q", bin=alt.Bin(maxbins=20), title="Điểm IMDB"),
                alt.Y('count()', title='Số lượng phim')
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Không có dữ liệu điểm số IMDB.")

    @staticmethod
    def draw_budget_vs_revenue(df):
        st.subheader("Tương quan: Kinh phí vs Doanh thu toàn cầu")
        st.markdown("*Bài toán: Phim đầu tư lớn có chắc chắn lãi không?*")
        valid_df = df.dropna(subset=['Production Budget', 'Worldwide Gross'])
        if not valid_df.empty:
            # Biểu đồ Scatter Plot phân tích kinh phí và doanh thu
            chart = alt.Chart(valid_df).mark_circle(size=60, opacity=0.6).encode(
                x=alt.X('Production Budget:Q', title='Kinh phí sản xuất ($)'),
                y=alt.Y('Worldwide Gross:Q', title='Doanh thu toàn cầu ($)'),
                color=alt.Color('Major Genre:N', legend=alt.Legend(title="Thể loại")),
                tooltip=['Title', 'Production Budget', 'Worldwide Gross', 'IMDB Rating']
            ).interactive().properties(height=450)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Không có đủ dữ liệu về Kinh phí và Doanh thu.")


# ==========================================
# HÀM ĐIỀU KHIỂN CHÍNH (MAIN APP)
# ==========================================
def main():
    st.set_page_config(page_title="Movie Explorer", layout="wide")

    # --- BƯỚC 1: LOAD DATA ---
    df = DataLoader.load_and_clean_data("movies.csv")

    # --- BƯỚC 2: SIDEBAR UI ---
    st.sidebar.title("Movie Explorer")
    st.sidebar.markdown("Dự án khám phá dữ liệu điện ảnh")
    st.sidebar.markdown("---")

    # --- BƯỚC 3 & 4: FILTER LOGIC ---
    st.sidebar.header("Bộ lọc Dữ liệu")

    # Lọc theo năm (Slider)
    min_year = int(df['Year'].min())
    max_year = int(df['Year'].max())
    selected_years = st.sidebar.slider(
        "Chọn khoảng thời gian (Năm phát hành):",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )

    # Lọc theo thể loại (Multiselect)
    genres = df['Major Genre'].unique().tolist()
    # Sắp xếp thể loại, đưa 'Unknown' xuống cuối danh sách cho logic
    genres.sort(key=lambda x: (x == 'Unknown', x))

    selected_genres = st.sidebar.multiselect(
        "Chọn Thể loại:",
        options=genres,
        default=genres[:3] if len(genres) >= 3 else genres
    )

    # Áp dụng bộ lọc lên DataFrame
    mask = (df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1])
    if selected_genres:
        mask = mask & (df['Major Genre'].isin(selected_genres))

    filtered_df = df[mask]

    # --- BƯỚC 5: DATA DISPLAY ---
    st.title("Phân tích Dữ liệu Phim")
    st.write(f"**Tổng số phim tìm thấy:** {len(filtered_df)}")

    # Hiển thị bảng dữ liệu với các cột quan trọng
    display_cols = ['Title', 'Year', 'Major Genre', 'IMDB Rating', 'Production Budget', 'Worldwide Gross']
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    st.markdown("---")

    # --- BƯỚC 6: VISUALIZATION (Gọi từ Class) ---
    drawer = ChartDrawer()

    # Chia cột cho 2 biểu đồ đầu tiên
    col1, col2 = st.columns(2)
    with col1:
        # Biểu đồ cột: Số lượng phim theo năm
        drawer.draw_movies_per_year(filtered_df)

    with col2:
        # Biểu đồ phân bố IMDB Rating
        drawer.draw_imdb_distribution(filtered_df)

    st.markdown("---")

    # Biểu đồ Scatter Plot ở dưới cùng chiếm toàn bộ chiều rộng
    drawer.draw_budget_vs_revenue(filtered_df)


if __name__ == "__main__":
    main()
