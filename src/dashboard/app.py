import streamlit as st
import pandas as pd
import boto3
import time
import plotly.express as px
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Visual Governance Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Look
st.markdown("""
    <style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Metrics Styling */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stMetric {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Charts Container */
    .stPlotlyChart {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AWS HELPERS ---
def run_athena_query(query, database, s3_output):
    # Ensure S3 output path ends with a slash
    if s3_output and not s3_output.endswith('/'):
        s3_output += '/'
        
    athena = boto3.client('athena', region_name='us-east-1')
    try:
        response = athena.start_query_execution(
            QueryString=query.strip(),
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': s3_output}
        )
        query_execution_id = response['QueryExecutionId']
        
        while True:
            execution = athena.get_query_execution(QueryExecutionId=query_execution_id)
            status = execution['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)
            
        if status == 'SUCCEEDED':
            results = athena.get_query_results(QueryExecutionId=query_execution_id)
            rows = results['ResultSet']['Rows']
            if len(rows) <= 1: return pd.DataFrame()
            column_names = [col['Name'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            data = [[val.get('VarCharValue', None) for val in row['Data']] for row in rows[1:]]
            return pd.DataFrame(data, columns=column_names)
        else:
            fail_msg = execution.get('QueryExecution', {}).get('Status', {}).get('StateChangeReason', 'Unknown Error')
            st.error(f"Athena Query Failed: {fail_msg}")
            return None
    except Exception as e:
        st.error(f"Athena API Error: {e}")
        return None

def upload_to_s3(file_bytes, bucket, file_name):
    s3 = boto3.client('s3', region_name='us-east-1')
    try:
        s3.put_object(Bucket=bucket, Key=f"uploaded-images/{file_name}", Body=file_bytes)
        return True
    except Exception as e:
        st.error(f"S3 Upload Error: {e}")
        return False

def analyze_image_rekognition(file_bytes):
    rekognition = boto3.client('rekognition', region_name='us-east-1')
    try:
        # Detect Moderation Labels (Safety)
        mod_response = rekognition.detect_moderation_labels(Image={'Bytes': file_bytes})
        mod_labels = mod_response.get('ModerationLabels', [])
        
        # Detect General Labels (to check if image is blank)
        gen_response = rekognition.detect_labels(Image={'Bytes': file_bytes}, MaxLabels=5)
        gen_labels = gen_response.get('Labels', [])
        
        harmful_score = max([l['Confidence'] for l in mod_labels]) if mod_labels else 0
        
        return {
            "harmful": round(harmful_score, 1),
            "safe": round(100 - harmful_score, 1),
            "raw_labels": mod_labels,
            "is_blank": (len(mod_labels) == 0 and len(gen_labels) == 0)
        }
    except Exception as e:
        st.error(f"Rekognition Error: {e}")
        return None

# --- SIDEBAR & AUTH ---
st.sidebar.title("🛡️ Governance Settings")
st.sidebar.markdown("Configure your AWS connection here.")

database_name = st.sidebar.text_input("Athena Database", value="visual_governance_db")
raw_bucket = st.sidebar.text_input("Raw Image Bucket", value="visual-governance-raw-urja")
analytics_bucket = st.sidebar.text_input("Analytics Bucket", value="visual-governance-analytics-urja")
s3_output = st.sidebar.text_input("Query Output Bucket (S3)", value="s3://visual-governance-analytics-urja/athena-results/")

st.sidebar.divider()
st.sidebar.subheader("📅 Data Filters")
today = datetime.now()
start_date = st.sidebar.date_input("Start Date", today.replace(day=1))
end_date = st.sidebar.date_input("End Date", today)

st.sidebar.divider()
if st.sidebar.button("Refresh Results", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("Sync S3 Partitions", use_container_width=True):
    with st.spinner("Repairing Athena metadata..."):
        run_athena_query(f"MSCK REPAIR TABLE moderation_results", database_name, s3_output)
        run_athena_query(f"MSCK REPAIR TABLE label_results", database_name, s3_output)
        st.success("S3 partitions synchronized!")
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("🛡️ Automated Visual Governance Dashboard")
st.subheader("Transforming raw pixels into actionable safety insights")

if not analytics_bucket:
    st.info("💡 Please enter your Athena Query Output Bucket in the sidebar to load live data.")
    
    # Showcase with Mock Data if no bucket provided
    st.warning("⚠️ Showing dummy data for demonstration. Connect your bucket for live insights.")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scanned", "1,284", "+15%")
    col2.metric("Flagged Images", "42", "-2%", delta_color="inverse")
    col3.metric("Safe Ratio", "96.7%", "+0.5%")
    col4.metric("Avg Confidence", "94.2%", "+1.2%")
    
    st.divider()
    
    c1, c2 = st.columns(2)
    
    mock_mod = pd.DataFrame({
        'category': ['Violence', 'Suggestive', 'Hate Symbols', 'Explicit'],
        'count': [15, 12, 10, 5]
    })
    fig1 = px.pie(mock_mod, values='count', names='category', title="Unsafe Categories Distribution", hole=0.4, template="plotly_dark")
    c1.plotly_chart(fig1, use_container_width=True)
    
    mock_trends = pd.DataFrame({
        'Date': pd.date_range(start='2026-03-01', periods=10),
        'Uploads': [50, 60, 45, 80, 70, 90, 110, 85, 95, 105]
    })
    fig2 = px.line(mock_trends, x='Date', y='Uploads', title="Upload Trends (Last 10 Days)", template="plotly_dark")
    c2.plotly_chart(fig2, use_container_width=True)

else:
    # LIVE DATA MODE
    try:
        tab1, tab2 = st.tabs(["📊 Global Analytics", "🔍 Real-time Analysis"])

        with tab1:
            # 1. Global Aggregated Analysis
            query_agg = f"""
                SELECT 
                    COUNT(DISTINCT image_name) as total_imgs,
                    AVG(max_harmful) as avg_h
                FROM (
                    SELECT image_name, MAX(CASE WHEN label_name != 'SAFE' THEN confidence_score ELSE 0 END) as max_harmful
                    FROM moderation_results
                    GROUP BY image_name
                )
            """.strip()
            df_agg = run_athena_query(query_agg, database_name, s3_output)
            
            total_imgs = int(df_agg['total_imgs'][0]) if df_agg is not None and not df_agg.empty else 0
            avg_harmful = float(df_agg['avg_h'][0]) if df_agg is not None and not df_agg.empty and df_agg['avg_h'][0] is not None else 0
            avg_safe = 100 - avg_harmful if total_imgs > 0 else 0
            
            st.markdown(f"### 🌐 System-Wide Intelligence")
            st.write(f"Aggregated summary of **{total_imgs:,}** images stored in S3.")
            
            m1, m2 = st.columns(2)
            with m1:
                st.write(f"⚠️ **Average Harmful: {avg_harmful:.1f}%**")
                st.progress(avg_harmful / 100)
            with m2:
                st.write(f"✅ **Average Safe: {avg_safe:.1f}%**")
                st.progress(avg_safe / 100)
            
            st.divider()
            
            # 2. Charts
            c1, c2 = st.columns(2)
            
            # Category Breakdown
            query_cat = f"""
                SELECT label_name, COUNT(DISTINCT image_name) as count 
                FROM moderation_results 
                WHERE label_name != 'SAFE' 
                AND year = '{start_date.year}' 
                AND month = '{start_date.month:02}'
                AND day BETWEEN '{start_date.day:02}' AND '{end_date.day:02}'
                GROUP BY label_name 
                ORDER BY count DESC
            """.strip()
            df_cat = run_athena_query(query_cat, database_name, s3_output)
            if df_cat is not None and not df_cat.empty:
                df_cat['count'] = pd.to_numeric(df_cat['count'])
                fig1 = px.bar(
                    df_cat, x='label_name', y='count', color='label_name', 
                    title="Violation Categories (By Date Range)",
                    color_discrete_sequence=px.colors.qualitative.Vivid,
                    template="plotly_dark"
                )
                fig1.update_layout(showlegend=False)
                c1.plotly_chart(fig1, use_container_width=True)
            else:
                c1.info("No moderation violations found in the selected date range.")
            
            # Trends
            query_trends = f"""
                SELECT concat(year, '-', month, '-', day) as day, COUNT(DISTINCT image_name) as count 
                FROM label_results 
                WHERE year = '{start_date.year}' 
                AND month = '{start_date.month:02}'
                AND day BETWEEN '{start_date.day:02}' AND '{end_date.day:02}'
                GROUP BY year, month, day 
                ORDER BY day ASC
            """.strip()
            df_trends = run_athena_query(query_trends, database_name, s3_output)
            if df_trends is not None and not df_trends.empty:
                df_trends['count'] = pd.to_numeric(df_trends['count'])
                fig2 = px.line(
                    df_trends, x='day', y='count', markers=True, 
                    title="Daily Processing Volume", line_shape="spline", template="plotly_dark"
                )
                fig2.update_traces(line_color='#38bdf8', marker=dict(size=12, symbol="diamond"))
                fig2.update_xaxes(type='category', title_text="Date") 
                fig2.update_yaxes(title_text="Images Processed")
                c2.plotly_chart(fig2, use_container_width=True)
            else:
                c2.info("No data available for the selected trend period.")

        with tab2:
            st.subheader("📤 AI Analysis Center")
            st.markdown("Upload any image to perform an **instant safety audit**. The image will be stored in your Data Lake for governance records.")
            
            uploaded_file = st.file_uploader("Upload Image (.jpg, .jpeg, .png)", type=["jpg", "jpeg", "png"])
            
            if uploaded_file:
                file_bytes = uploaded_file.read()
                
                u_col1, u_col2 = st.columns([1, 1.2])
                
                with u_col1:
                    st.image(file_bytes, caption="Image Preview", use_container_width=True)
                    
                with u_col2:
                    if st.button("🚀 Start Deep Analysis", use_container_width=True):
                        with st.spinner("Analyzing content safety..."):
                            # 1. Unique Filename
                            timestamp = int(time.time())
                            file_name = f"audit_{timestamp}_{uploaded_file.name}"
                            
                            # 2. Upload to S3
                            s3_success = upload_to_s3(file_bytes, raw_bucket, file_name)
                            
                            # 3. Rekognition Analysis
                            prediction = analyze_image_rekognition(file_bytes)
                            
                            if s3_success and prediction:
                                if prediction.get('is_blank'):
                                    st.warning("📭 **No images are detected**")
                                else:
                                    st.markdown("### 🎯 Safety Prediction")
                                    
                                    # Visual percentages
                                    h_pct = prediction['harmful']
                                    s_pct = prediction['safe']
                                    
                                    st.write(f"⚠️ **Harmful Content: {h_pct}%**")
                                    st.progress(h_pct / 100)
                                    
                                    st.write(f"✅ **Safe Content: {s_pct}%**")
                                    st.progress(s_pct / 100)
                                    
                                    if h_pct > 0:
                                        st.warning(f"Detected {len(prediction['raw_labels'])} moderation categories.")
                                        for label in prediction['raw_labels']:
                                            st.write(f"- **{label['Name']}**: {round(label['Confidence'], 1)}% confidence")
                                    else:
                                        st.success("No moderation violations detected. This content is safe.")
                                    
                                st.info(f"💾 Image archived in S3 as: `{file_name}`")
                            else:
                                st.error("Analysis pipeline failed. Check your AWS credentials and bucket configuration.")
            
    except Exception as e:
        st.error(f"Error occurring in dashboard: {e}")
        st.info("Ensure your AWS environment is active and permissions are granted.")

st.sidebar.markdown("---")
st.sidebar.caption("v1.0.0 | Built with Streamlit & Boto3")
